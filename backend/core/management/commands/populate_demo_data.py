from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, Iterable

from django.apps import apps
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone
from faker import Faker

from accounts.models import Organization, Profile
from analytics.models import EmployeeInsight, MeetingAnalysis
from employees.models import Employee
from meetings.models import EmployeeMeetingInsight, Meeting, MeetingParticipant, MeetingSpeakerMapping, MeetingTranscript


fake = Faker("en_IN")


DEPARTMENTS = [
    "Engineering",
    "Product",
    "HR",
    "Marketing",
    "Finance",
    "Customer Success",
]

MEETING_TYPES = [
    "1:1 Manager Meeting",
    "Performance Review Meeting",
    "Career Development Meeting",
    "Team Retrospective",
    "HR Feedback Meeting",
]

GOAL_TEMPLATES = [
    "Improve API latency",
    "Launch new product feature",
    "Increase customer retention",
    "Improve documentation quality",
    "Reduce sprint spillover",
    "Mentor junior team members",
    "Strengthen stakeholder communication",
    "Improve test automation coverage",
    "Optimize cloud cost",
]

STRENGTH_BANK = [
    "Strong ownership mindset",
    "Excellent stakeholder communication",
    "High-quality technical execution",
    "Collaboration and mentoring",
    "Consistent delivery under pressure",
    "Creative problem solving",
]

WEAKNESS_BANK = [
    "Needs better workload prioritization",
    "Can improve cross-team alignment",
    "Should delegate more effectively",
    "Needs to document decisions better",
    "Can improve proactive escalation",
    "Should improve meeting preparedness",
]

FEEDBACK_SNIPPETS = [
    "I feel the workload has increased significantly this quarter.",
    "We need better communication between product and engineering.",
    "Career growth conversations are improving but still inconsistent.",
    "Deadlines are often aggressive and impact work-life balance.",
    "Leadership communication has become clearer in recent months.",
    "Cross-functional handoffs are causing avoidable delays.",
    "I appreciate the support from my manager during difficult sprints.",
    "We should invest more in onboarding and internal documentation.",
]

SURVEY_QUESTIONS = [
    "I feel valued at work",
    "I see career growth opportunities",
    "I trust leadership decisions",
    "I can maintain a healthy work-life balance",
    "I get timely support from my manager",
    "My work contributes to company goals",
]

CONVERSATION_SNIPPETS = [
    "Can you review the pull request?",
    "The release deadline is approaching.",
    "Let us align on priorities for this sprint.",
    "I need help with the production issue root cause.",
    "Can we revisit the timeline for this dependency?",
    "Customer escalation came in, can we respond today?",
    "Thanks for helping with the incident yesterday.",
    "I need clarity on ownership for this action item.",
]

ATTRITION_REASONS = [
    "Low engagement",
    "High workload",
    "Poor manager relationship",
    "Limited growth opportunities",
    "Compensation concerns",
    "Burnout due to sustained overtime",
]

POSITIVE_LINES = [
    "I feel supported by the team and the priorities are clear.",
    "The collaboration this sprint was smooth and productive.",
    "I am excited about the roadmap and my growth plan.",
]

NEUTRAL_LINES = [
    "The workload is manageable, but we need better planning discipline.",
    "Progress is steady though dependencies still slow us down.",
    "I can deliver, but some requirements are still ambiguous.",
]

NEGATIVE_LINES = [
    "I am overloaded and the pace has not been sustainable.",
    "I feel blocked by unclear decisions and late requirement changes.",
    "The team morale has dipped because of repeated deadline pressure.",
]


@dataclass
class OptionalModels:
    company: Any | None = None
    department: Any | None = None
    performance_review: Any | None = None
    goal: Any | None = None
    feedback: Any | None = None
    survey_response: Any | None = None
    conversation: Any | None = None
    attrition_risk: Any | None = None
    sentiment_analysis: Any | None = None


class Command(BaseCommand):
    help = "Populate enterprise-scale demo data for HR intelligence and meeting analytics"

    def add_arguments(self, parser):
        parser.add_argument("--employees", type=int, default=60)
        parser.add_argument("--meetings", type=int, default=200)
        parser.add_argument("--conversations", type=int, default=500)
        parser.add_argument("--feedback", type=int, default=200)
        parser.add_argument("--surveys", type=int, default=300)
        parser.add_argument("--reviews", type=int, default=180)
        parser.add_argument("--seed", type=int, default=42)

    def handle(self, *args, **options):
        random.seed(options["seed"])
        Faker.seed(options["seed"])

        if connection.vendor != "postgresql":
            self.stdout.write(self.style.WARNING("Current DB is not PostgreSQL. Proceeding with configured DB anyway."))

        target_employees = max(60, min(80, options["employees"]))
        target_meetings = max(200, options["meetings"])
        target_conversations = max(500, options["conversations"])
        target_feedback = max(200, options["feedback"])
        target_surveys = max(300, options["surveys"])
        target_reviews = max(180, options["reviews"])

        optional = self._discover_optional_models()

        with transaction.atomic():
            org = self._ensure_org()
            hr_users = self._ensure_hr_users(org)
            departments = self._ensure_departments(optional, org)
            employees = self._create_employees(org, departments, target_employees)
            meetings = self._create_meetings(org, hr_users, employees, target_meetings)
            self._create_performance_reviews(optional, employees, target_reviews)
            self._create_goals(optional, employees)
            self._create_feedback(optional, employees, target_feedback)
            self._create_surveys(optional, employees, target_surveys)
            self._create_conversations(optional, employees, target_conversations)
            self._create_attrition(optional, employees)
            self._create_sentiment_analyses(optional, meetings)

        self.stdout.write(self.style.SUCCESS("Demo data generation completed successfully."))

    def _discover_optional_models(self) -> OptionalModels:
        return OptionalModels(
            company=self._get_model_by_name("Company"),
            department=self._get_model_by_name("Department"),
            performance_review=self._get_model_by_name("PerformanceReview"),
            goal=self._get_model_by_name("Goal"),
            feedback=self._get_model_by_name("Feedback"),
            survey_response=self._get_model_by_name("SurveyResponse"),
            conversation=self._get_model_by_name("Conversation"),
            attrition_risk=self._get_model_by_name("AttritionRisk"),
            sentiment_analysis=self._get_model_by_name("SentimentAnalysis"),
        )

    def _get_model_by_name(self, model_name: str):
        for model in apps.get_models():
            if model.__name__.lower() == model_name.lower():
                return model
        return None

    def _has_field(self, model, field_name: str) -> bool:
        return any(field.name == field_name for field in model._meta.get_fields())

    def _set_if_field(self, model, payload: dict[str, Any], field_name: str, value: Any):
        if self._has_field(model, field_name):
            payload[field_name] = value

    def _ensure_org(self) -> Organization:
        org, _ = Organization.objects.get_or_create(
            organization_name="NovaTech Solutions",
            defaults={
                "industry": "Software and AI",
            },
        )
        return org

    def _ensure_hr_users(self, org: Organization) -> dict[str, User]:
        users_config = [
            ("chro", "CHRO", "CHR", "Chief HR Officer"),
            ("hrbp", "HR BP", "HR", "HR Business Partner"),
            ("hrstaff", "HR Staff", "HR", "HR Staff"),
        ]

        result = {}
        for username, full_name, role, designation in users_config:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": full_name.split()[0],
                    "last_name": " ".join(full_name.split()[1:]),
                    "email": f"{username}@novatech.com",
                },
            )
            if created:
                user.set_password("Pass@1234")
                user.save(update_fields=["password"])

            profile = user.profile
            profile.role = role
            profile.organization = org
            profile.designation = designation
            profile.department = "HR"
            profile.save()
            result[username] = user

        return result

    def _ensure_departments(self, optional: OptionalModels, org: Organization) -> dict[str, Any]:
        mapping: dict[str, Any] = {}
        if optional.department is None:
            for name in DEPARTMENTS:
                mapping[name] = name
            return mapping

        rows = []
        for name in DEPARTMENTS:
            defaults = {}
            if self._has_field(optional.department, "name"):
                defaults["name"] = name
            elif self._has_field(optional.department, "department_name"):
                defaults["department_name"] = name

            if not defaults:
                continue

            lookup_key = "name" if "name" in defaults else "department_name"
            obj, _ = optional.department.objects.get_or_create(**{lookup_key: defaults[lookup_key]})
            if self._has_field(optional.department, "organization") and getattr(obj, "organization_id", None) is None:
                obj.organization = org
                obj.save(update_fields=["organization"])
            mapping[name] = obj

        return mapping

    def _create_employees(self, org: Organization, departments: dict[str, Any], target_count: int) -> list[Employee]:
        existing = list(Employee.objects.filter(organization=org))
        if len(existing) >= target_count:
            return existing[:target_count]

        dept_heads: dict[str, Employee] = {}
        employees_to_create = []

        available_roles = {
            "Engineering": ["Engineering Manager", "Senior Software Engineer", "Backend Engineer", "Frontend Engineer", "SRE"],
            "Product": ["Product Manager", "Senior Product Manager", "Product Analyst"],
            "HR": ["HR Manager", "HR Business Partner", "Talent Specialist"],
            "Marketing": ["Marketing Manager", "Growth Specialist", "Content Strategist"],
            "Finance": ["Finance Manager", "Financial Analyst", "FP&A Specialist"],
            "Customer Success": ["Customer Success Manager", "Implementation Specialist", "Support Lead"],
        }

        current_count = len(existing)
        needed = target_count - current_count

        while len(employees_to_create) < needed:
            dept = DEPARTMENTS[(current_count + len(employees_to_create)) % len(DEPARTMENTS)]
            name = fake.name()
            email = f"{name.lower().replace(' ', '.')}@novatech.com"
            role = random.choice(available_roles[dept])

            manager_name = ""
            if dept in dept_heads:
                manager_name = dept_heads[dept].name

            row = Employee(
                name=name,
                role=role,
                department=dept,
                join_date=fake.date_between(start_date="-8y", end_date="-30d"),
                organization=org,
                manager=manager_name,
                email=self._unique_employee_email(email),
            )
            employees_to_create.append(row)

        created = Employee.objects.bulk_create(employees_to_create, batch_size=200)

        all_employees = existing + created
        by_dept: dict[str, list[Employee]] = defaultdict(list)
        for emp in all_employees:
            by_dept[emp.department].append(emp)

        updates = []
        for dept, rows in by_dept.items():
            rows.sort(key=lambda e: e.join_date)
            head = rows[0]
            dept_heads[dept] = head
            for idx, emp in enumerate(rows):
                manager = head if idx > 0 else None
                manager_name = manager.name if manager else ""
                manager_user = None
                if manager and manager.email and manager.email in {"chro@novatech.com", "hrbp@novatech.com", "hrstaff@novatech.com"}:
                    manager_user = User.objects.filter(email=manager.email).first()
                if emp.manager != manager_name or emp.manager_user_id != (manager_user.id if manager_user else None):
                    emp.manager = manager_name
                    emp.manager_user = manager_user
                    updates.append(emp)

        if updates:
            Employee.objects.bulk_update(updates, ["manager", "manager_user"], batch_size=200)

        all_employees = list(Employee.objects.filter(organization=org)[:target_count])

        insight_rows = []
        for emp in all_employees:
            performance = round(random.uniform(2.2, 4.9), 2)
            engagement = round(random.uniform(2.0, 4.8), 2)
            topics = [
                {"topic": random.choice(["Career Growth", "Workload", "Manager Support", "Team Collaboration"]), "relevance": round(random.uniform(0.4, 0.95), 2)}
                for _ in range(3)
            ]
            insight_rows.append(
                EmployeeInsight(
                    employee=emp,
                    topics=topics,
                    career_goals=random.choice([
                        "Grow into a people leadership role",
                        "Become a principal individual contributor",
                        "Strengthen product strategy ownership",
                        "Improve cross-functional influence",
                    ]),
                    concerns=random.choice([
                        "Workload fluctuations during release cycles",
                        "Need clearer growth path",
                        "Better prioritization from leadership needed",
                        "No major concerns",
                    ]),
                    burnout_risk=round(max(0.0, 1 - (engagement / 5.0)), 2),
                    strengths=random.choice(STRENGTH_BANK),
                )
            )

        EmployeeInsight.objects.bulk_create(insight_rows, batch_size=200, ignore_conflicts=True)
        return all_employees

    def _unique_employee_email(self, email: str) -> str:
        base = email
        idx = 1
        while Employee.objects.filter(email=email).exists():
            local, domain = base.split("@", 1)
            email = f"{local}{idx}@{domain}"
            idx += 1
        return email

    def _create_meetings(self, org: Organization, hr_users: dict[str, User], employees: list[Employee], target_meetings: int) -> list[Meeting]:
        existing_count = Meeting.objects.filter(organization=org).count()
        to_create = max(0, target_meetings - existing_count)
        if to_create == 0:
            return list(Meeting.objects.filter(organization=org).order_by("-id")[:target_meetings])

        meeting_rows: list[Meeting] = []
        today = timezone.now().date()

        for _ in range(to_create):
            owner = random.choice(employees)
            meeting_type = random.choice(MEETING_TYPES)
            meeting_title = f"{meeting_type} - {owner.department}"
            meeting_date = fake.date_between(start_date="-180d", end_date=today)
            uploader = random.choice(list(hr_users.values()))

            mood = random.choices(["positive", "neutral", "negative"], weights=[35, 40, 25], k=1)[0]
            transcript_text, summary, sentiment, key_topics = self._generate_meeting_text_bundle(owner.name, mood)

            meeting_rows.append(
                Meeting(
                    organization=org,
                    meeting_title=meeting_title,
                    department=owner.department,
                    meeting_date=meeting_date,
                    uploaded_by=uploader,
                    transcript_status=Meeting.TRANSCRIPT_STATUS_COMPLETED,
                    employee=owner,
                    date=meeting_date,
                    transcript=transcript_text,
                    summary=summary,
                    sentiment_score=sentiment,
                    key_topics=key_topics,
                )
            )

        created_meetings = Meeting.objects.bulk_create(meeting_rows, batch_size=200)

        participants_rows: list[MeetingParticipant] = []
        transcript_rows: list[MeetingTranscript] = []
        mapping_rows: list[MeetingSpeakerMapping] = []
        analysis_rows: list[MeetingAnalysis] = []
        employee_insight_rows: list[EmployeeMeetingInsight] = []

        for meeting in created_meetings:
            participant_count = random.randint(2, 6)
            participants = random.sample(employees, k=min(participant_count, len(employees)))
            if meeting.employee not in participants:
                participants[0] = meeting.employee

            speaker_index = 1
            speaker_to_employee = {}

            for participant in participants:
                participants_rows.append(MeetingParticipant(meeting=meeting, employee=participant))
                label = f"Speaker_{speaker_index}"
                speaker_index += 1
                mapping_rows.append(MeetingSpeakerMapping(meeting=meeting, speaker_label=label, employee=participant))
                speaker_to_employee[label] = participant

            transcript_segments = self._build_transcript_segments(speaker_to_employee)
            for seg in transcript_segments:
                transcript_rows.append(
                    MeetingTranscript(
                        meeting=meeting,
                        speaker=seg["speaker"],
                        text=seg["text"],
                        start_time=seg["start"],
                        end_time=seg["end"],
                    )
                )

            by_employee_sentiment = {}
            durations = defaultdict(float)
            turns = defaultdict(int)
            interruptions = defaultdict(int)
            for seg in transcript_segments:
                emp = speaker_to_employee.get(seg["speaker"])
                if not emp:
                    continue
                duration = max(0.0, seg["end"] - seg["start"])
                durations[emp.id] += duration
                turns[emp.id] += 1
                if random.random() < 0.1:
                    interruptions[emp.id] += 1

            total_duration = max(1.0, sum(durations.values()))
            for emp in participants:
                score = round(random.uniform(0.2, 0.9), 3)
                by_employee_sentiment[str(emp.id)] = {
                    "label": "positive" if score > 0.6 else "neutral" if score > 0.4 else "negative",
                    "scores": {
                        "positive": score,
                        "neutral": round(min(1.0, max(0.0, 1.0 - abs(score - 0.5))), 3),
                        "negative": round(1.0 - score, 3),
                    },
                }

                engagement = durations[emp.id] / total_duration
                employee_insight_rows.append(
                    EmployeeMeetingInsight(
                        employee=emp,
                        meeting=meeting,
                        participation_duration=round(durations[emp.id], 2),
                        sentiment_score=round(score, 3),
                        engagement_score=round(engagement, 3),
                        speaking_turns=turns[emp.id],
                        interruption_signals=interruptions[emp.id],
                    )
                )

            avg_positive = round(sum(v["scores"]["positive"] for v in by_employee_sentiment.values()) / max(1, len(by_employee_sentiment)), 3)
            overall = {
                "label": "positive" if avg_positive > 0.6 else "neutral" if avg_positive > 0.4 else "negative",
                "scores": {
                    "positive": avg_positive,
                    "neutral": round(min(1.0, max(0.0, 1.0 - abs(avg_positive - 0.5))), 3),
                    "negative": round(1.0 - avg_positive, 3),
                },
            }

            analysis_rows.append(
                MeetingAnalysis(
                    meeting=meeting,
                    transcript=meeting.transcript,
                    summary=meeting.summary,
                    employee_sentiment_scores={
                        "overall": overall,
                        "by_employee": by_employee_sentiment,
                        "by_speaker": {
                            label: by_employee_sentiment.get(str(emp.id), overall)
                            for label, emp in speaker_to_employee.items()
                        },
                    },
                    participation_score=round(sum(item.engagement_score for item in employee_insight_rows if item.meeting_id == meeting.id) / max(1, len(participants)), 3),
                    collaboration_signals={"level": random.choice(["low", "medium", "high"]), "keyword_hits": random.randint(1, 8)},
                    engagement_signals={"level": random.choice(["low", "medium", "high"]), "keyword_hits": random.randint(1, 10)},
                    conflict_detection={"level": random.choice(["low", "medium", "high"]), "keyword_hits": random.randint(0, 6)},
                    speaker_mapping={
                        "speakers": {label: emp.id for label, emp in speaker_to_employee.items()},
                    },
                )
            )

        MeetingParticipant.objects.bulk_create(participants_rows, batch_size=500, ignore_conflicts=True)
        MeetingSpeakerMapping.objects.bulk_create(mapping_rows, batch_size=500, ignore_conflicts=True)
        MeetingTranscript.objects.bulk_create(transcript_rows, batch_size=1000)
        MeetingAnalysis.objects.bulk_create(analysis_rows, batch_size=200, ignore_conflicts=True)
        EmployeeMeetingInsight.objects.bulk_create(employee_insight_rows, batch_size=1000, ignore_conflicts=True)

        return list(Meeting.objects.filter(organization=org).order_by("-id")[:target_meetings])

    def _generate_meeting_text_bundle(self, employee_name: str, mood: str) -> tuple[str, str, float, list[dict[str, Any]]]:
        lines = [
            f"Manager: Let us review progress and wellbeing this month, {employee_name}.",
            f"{employee_name}: I want to discuss priorities, growth, and team coordination.",
        ]

        if mood == "positive":
            lines.extend(random.sample(POSITIVE_LINES, k=2))
            sentiment = round(random.uniform(0.68, 0.92), 3)
        elif mood == "negative":
            lines.extend(random.sample(NEGATIVE_LINES, k=2))
            sentiment = round(random.uniform(0.12, 0.39), 3)
        else:
            lines.extend(random.sample(NEUTRAL_LINES, k=2))
            sentiment = round(random.uniform(0.41, 0.64), 3)

        lines.append("Manager: Let us convert these points into clear action items and follow-ups.")

        transcript = "\n".join(lines)
        summary = (
            "Discussion covered workload, priorities, collaboration, and career growth. "
            "Actions were agreed for manager support, clearer planning, and follow-up checkpoints."
        )
        topics = [
            {"topic": "Workload", "relevance": round(random.uniform(0.5, 0.95), 2)},
            {"topic": "Career Development", "relevance": round(random.uniform(0.4, 0.92), 2)},
            {"topic": "Team Collaboration", "relevance": round(random.uniform(0.45, 0.9), 2)},
        ]
        return transcript, summary, sentiment, topics

    def _build_transcript_segments(self, speaker_to_employee: dict[str, Employee]) -> list[dict[str, Any]]:
        segments = []
        current = 0.0
        labels = list(speaker_to_employee.keys())
        random.shuffle(labels)

        segment_count = random.randint(6, 12)
        for i in range(segment_count):
            label = labels[i % len(labels)]
            mood = random.choices(["positive", "neutral", "negative"], weights=[35, 40, 25], k=1)[0]
            if mood == "positive":
                text = random.choice(POSITIVE_LINES)
            elif mood == "negative":
                text = random.choice(NEGATIVE_LINES)
            else:
                text = random.choice(NEUTRAL_LINES)

            duration = random.uniform(8.0, 28.0)
            start = current
            end = current + duration
            current = end + random.uniform(0.2, 3.0)

            segments.append(
                {
                    "speaker": label,
                    "text": text,
                    "start": round(start, 2),
                    "end": round(end, 2),
                }
            )

        return segments

    def _create_performance_reviews(self, optional: OptionalModels, employees: list[Employee], target_reviews: int):
        model = optional.performance_review
        if model is None:
            return

        rows = []
        for _ in range(target_reviews):
            employee = random.choice(employees)
            reviewer = random.choice(employees)
            payload = {}
            self._set_if_field(model, payload, "employee", employee)
            self._set_if_field(model, payload, "reviewer", reviewer)
            self._set_if_field(model, payload, "rating", round(random.uniform(1.5, 5.0), 2))
            self._set_if_field(model, payload, "strengths", random.choice(STRENGTH_BANK))
            self._set_if_field(model, payload, "weaknesses", random.choice(WEAKNESS_BANK))
            self._set_if_field(model, payload, "review_date", fake.date_between(start_date="-18m", end_date="today"))
            self._set_if_field(model, payload, "promotion_recommendation", random.random() < 0.25)
            rows.append(model(**payload))

        if rows:
            model.objects.bulk_create(rows, batch_size=300)

    def _create_goals(self, optional: OptionalModels, employees: list[Employee]):
        model = optional.goal
        if model is None:
            return

        rows = []
        for employee in employees:
            for _ in range(random.randint(3, 5)):
                payload = {}
                self._set_if_field(model, payload, "employee", employee)
                self._set_if_field(model, payload, "goal_title", random.choice(GOAL_TEMPLATES))
                self._set_if_field(model, payload, "progress", random.randint(5, 98))
                self._set_if_field(model, payload, "deadline", fake.date_between(start_date="today", end_date="+9M"))
                self._set_if_field(model, payload, "status", random.choice(["Not Started", "On Track", "At Risk", "Completed"]))
                rows.append(model(**payload))

        if rows:
            model.objects.bulk_create(rows, batch_size=400)

    def _create_feedback(self, optional: OptionalModels, employees: list[Employee], target_feedback: int):
        model = optional.feedback
        if model is None:
            return

        rows = []
        for _ in range(target_feedback):
            employee = random.choice(employees)
            text = random.choice(FEEDBACK_SNIPPETS)
            payload = {}
            self._set_if_field(model, payload, "employee", employee)
            self._set_if_field(model, payload, "department", employee.department)
            self._set_if_field(model, payload, "feedback_text", text)
            self._set_if_field(model, payload, "sentiment", random.choice(["positive", "neutral", "negative"]))
            ts = fake.date_time_between(start_date="-150d", end_date="now", tzinfo=timezone.utc)
            self._set_if_field(model, payload, "timestamp", ts)
            self._set_if_field(model, payload, "created_at", ts)
            rows.append(model(**payload))

        if rows:
            model.objects.bulk_create(rows, batch_size=300)

    def _create_surveys(self, optional: OptionalModels, employees: list[Employee], target_surveys: int):
        model = optional.survey_response
        if model is None:
            return

        rows = []
        for _ in range(target_surveys):
            employee = random.choice(employees)
            payload = {}
            self._set_if_field(model, payload, "employee", employee)
            self._set_if_field(model, payload, "question", random.choice(SURVEY_QUESTIONS))
            self._set_if_field(model, payload, "rating", random.randint(1, 5))
            ts = fake.date_time_between(start_date="-120d", end_date="now", tzinfo=timezone.utc)
            self._set_if_field(model, payload, "timestamp", ts)
            self._set_if_field(model, payload, "created_at", ts)
            rows.append(model(**payload))

        if rows:
            model.objects.bulk_create(rows, batch_size=400)

    def _create_conversations(self, optional: OptionalModels, employees: list[Employee], target_conversations: int):
        model = optional.conversation
        if model is None:
            return

        rows = []
        for _ in range(target_conversations):
            sender = random.choice(employees)
            receiver = random.choice([e for e in employees if e.id != sender.id])
            payload = {}
            self._set_if_field(model, payload, "sender", sender)
            self._set_if_field(model, payload, "receiver", receiver)
            self._set_if_field(model, payload, "message", random.choice(CONVERSATION_SNIPPETS))
            ts = fake.date_time_between(start_date="-90d", end_date="now", tzinfo=timezone.utc)
            self._set_if_field(model, payload, "timestamp", ts)
            self._set_if_field(model, payload, "created_at", ts)
            rows.append(model(**payload))

        if rows:
            model.objects.bulk_create(rows, batch_size=500)

    def _create_attrition(self, optional: OptionalModels, employees: list[Employee]):
        model = optional.attrition_risk
        if model is None:
            return

        high_risk_count = max(6, int(len(employees) * 0.12))
        high_risk_ids = {emp.id for emp in random.sample(employees, k=min(high_risk_count, len(employees)))}

        rows = []
        for employee in employees:
            is_high = employee.id in high_risk_ids
            risk_score = round(random.uniform(0.65, 0.95), 3) if is_high else round(random.uniform(0.1, 0.6), 3)
            risk_level = "High" if risk_score >= 0.75 else "Medium" if risk_score >= 0.45 else "Low"
            payload = {}
            self._set_if_field(model, payload, "employee", employee)
            self._set_if_field(model, payload, "risk_score", risk_score)
            self._set_if_field(model, payload, "risk_level", risk_level)
            self._set_if_field(model, payload, "reason", random.choice(ATTRITION_REASONS))
            rows.append(model(**payload))

        if rows:
            model.objects.bulk_create(rows, batch_size=300)

    def _create_sentiment_analyses(self, optional: OptionalModels, meetings: list[Meeting]):
        model = optional.sentiment_analysis
        if model is None:
            return

        rows = []
        for meeting in meetings:
            payload = {}
            score = round(float(meeting.sentiment_score or random.uniform(0.2, 0.9)), 3)
            emotion = "positive" if score > 0.6 else "neutral" if score > 0.4 else "negative"

            self._set_if_field(model, payload, "source_type", "meeting_transcript")
            self._set_if_field(model, payload, "source_id", meeting.id)
            self._set_if_field(model, payload, "sentiment_score", score)
            self._set_if_field(model, payload, "emotion", emotion)
            self._set_if_field(model, payload, "confidence", round(random.uniform(0.72, 0.98), 3))
            rows.append(model(**payload))

        if rows:
            model.objects.bulk_create(rows, batch_size=400)
