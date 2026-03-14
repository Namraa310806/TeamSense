"""Django management command to seed demo data."""
from django.core.management.base import BaseCommand
from employees.models import Employee
from meetings.models import Meeting
from analytics.models import EmployeeInsight
from datetime import date, timedelta
import random


SAMPLE_TRANSCRIPTS = [
    {
        'transcript': (
            "Meeting with Sarah about her quarterly goals. Sarah mentioned she wants to focus on "
            "leadership development this quarter. She expressed excitement about the new project management "
            "training opportunity. Her team collaboration has been excellent. She discussed her career goal "
            "of becoming a senior engineering manager within the next two years. Performance has been strong "
            "with all deliverables met ahead of schedule. She mentioned some concerns about the increasing "
            "workload but feels confident the team can handle it with proper prioritization."
        ),
        'summary': (
            "Key Points:\n• Sarah focused on leadership development goals\n"
            "• Excited about project management training\n"
            "• Career goal: Senior Engineering Manager in 2 years\n"
            "• All deliverables met ahead of schedule\n"
            "• Minor concern about increasing workload"
        ),
        'sentiment': 0.78,
        'topics': [{'topic': 'Career Development', 'relevance': 0.8}, {'topic': 'Performance', 'relevance': 0.6}],
    },
    {
        'transcript': (
            "One-on-one with James from the Data Science team. James expressed frustration with the lack of "
            "career growth opportunities in the current role. He feels his skills in machine learning are "
            "underutilized. James mentioned he's been approached by other companies. He wants more challenging "
            "projects and is concerned about the team morale declining. The recent project deadline caused "
            "significant stress and overtime. He suggested better resource allocation and clearer communication "
            "from leadership about company direction."
        ),
        'summary': (
            "Key Points:\n• James frustrated with limited career growth\n"
            "• Skills underutilized, approached by other companies\n"
            "• Team morale declining, recent deadline stress\n"
            "• Requests: challenging projects, better resource allocation\n"
            "• Wants clearer leadership communication"
        ),
        'sentiment': 0.32,
        'topics': [
            {'topic': 'Career Development', 'relevance': 0.9},
            {'topic': 'Work-Life Balance', 'relevance': 0.7},
            {'topic': 'Feedback', 'relevance': 0.6},
        ],
    },
    {
        'transcript': (
            "Performance review discussion with Priya. Priya has exceeded all KPIs for this quarter. "
            "Her productivity metrics show a 25% improvement from last quarter. She initiated and led "
            "the innovation sprint that resulted in three new feature proposals. Team members consistently "
            "praise her mentoring abilities. Priya is interested in exploring technical architecture roles. "
            "She feels good about the team dynamics and collaboration. No major concerns raised during "
            "the meeting. She's excited about the upcoming product launch."
        ),
        'summary': (
            "Key Points:\n• Exceeded all KPIs with 25% productivity improvement\n"
            "• Led innovation sprint: 3 new feature proposals\n"
            "• Strong mentoring praised by team\n"
            "• Interested in technical architecture roles\n"
            "• Excited about upcoming product launch"
        ),
        'sentiment': 0.89,
        'topics': [
            {'topic': 'Performance', 'relevance': 0.9},
            {'topic': 'Innovation', 'relevance': 0.7},
            {'topic': 'Career Development', 'relevance': 0.5},
        ],
    },
    {
        'transcript': (
            "Catch-up with Michael regarding project deadlines and team issues. Michael reported that "
            "the sprint deliverables are on track but identified a risk with the database migration. "
            "He mentioned increasing difficulty with cross-team collaboration. Several team members have "
            "complained about unclear requirements from stakeholders. Michael is concerned about burnout "
            "among developers who have been working overtime for three consecutive sprints. He suggested "
            "implementing a wellness program and more realistic sprint planning."
        ),
        'summary': (
            "Key Points:\n• Sprint deliverables on track, DB migration risk\n"
            "• Cross-team collaboration challenges\n"
            "• Unclear requirements from stakeholders\n"
            "• Developer burnout from 3 sprints of overtime\n"
            "• Suggests wellness program and realistic sprint planning"
        ),
        'sentiment': 0.41,
        'topics': [
            {'topic': 'Project Updates', 'relevance': 0.8},
            {'topic': 'Work-Life Balance', 'relevance': 0.7},
            {'topic': 'Team Dynamics', 'relevance': 0.6},
        ],
    },
    {
        'transcript': (
            "Discussion with Elena about her onboarding experience and initial impressions. Elena joined "
            "two months ago and has been adapting well to the team culture. She appreciates the structured "
            "mentoring program and the documentation quality. Her goal is to contribute to the core platform "
            "within the next quarter. She asked about training budget for a cloud certification. Overall "
            "positive experience with great team collaboration. She suggested improving the onboarding "
            "checklist with more hands-on exercises."
        ),
        'summary': (
            "Key Points:\n• Adapting well after 2 months\n"
            "• Appreciates mentoring program and documentation\n"
            "• Goal: contribute to core platform next quarter\n"
            "• Requested cloud certification training budget\n"
            "• Suggests more hands-on onboarding exercises"
        ),
        'sentiment': 0.75,
        'topics': [
            {'topic': 'Career Development', 'relevance': 0.7},
            {'topic': 'Team Dynamics', 'relevance': 0.5},
            {'topic': 'Feedback', 'relevance': 0.4},
        ],
    },
    {
        'transcript': (
            "Quarterly check-in with David from the Sales Engineering team. David has been consistently "
            "meeting his sales targets and customer satisfaction scores are high. However, he expressed "
            "concern about the compensation package not being competitive with market rates. He mentioned "
            "colleagues at competitor companies earning significantly more. He also raised the issue of "
            "limited promotion opportunities in the current team structure. Despite these concerns, he "
            "enjoys the company culture and team dynamics. He requested a formal salary review."
        ),
        'summary': (
            "Key Points:\n• Meeting sales targets, high customer satisfaction\n"
            "• Compensation concerns: not competitive with market\n"
            "• Colleagues at competitors earning more\n"
            "• Limited promotion opportunities\n"
            "• Requests formal salary review, enjoys culture"
        ),
        'sentiment': 0.45,
        'topics': [
            {'topic': 'Compensation', 'relevance': 0.9},
            {'topic': 'Career Development', 'relevance': 0.6},
            {'topic': 'Feedback', 'relevance': 0.5},
        ],
    },
    {
        'transcript': (
            "Follow-up meeting with Aisha about her team lead transition. Aisha has successfully "
            "taken over the mobile development team lead role. She implemented new code review processes "
            "that improved code quality by 30%. The team velocity has increased under her leadership. "
            "She's planning to introduce pair programming sessions and weekly architecture discussions. "
            "Her main challenge is balancing individual contributions with management responsibilities. "
            "Overall she feels supported by the organization and is thriving in the new role."
        ),
        'summary': (
            "Key Points:\n• Successfully transitioned to team lead\n"
            "• Code review process improved quality by 30%\n"
            "• Team velocity increased\n"
            "• Planning pair programming and architecture sessions\n"
            "• Challenge: balancing IC and management work"
        ),
        'sentiment': 0.82,
        'topics': [
            {'topic': 'Career Development', 'relevance': 0.8},
            {'topic': 'Performance', 'relevance': 0.7},
            {'topic': 'Team Dynamics', 'relevance': 0.6},
        ],
    },
    {
        'transcript': (
            "Urgent meeting with Tom about his workload concerns. Tom has been consistently working "
            "60+ hour weeks for the past month due to the critical release cycle. He expressed high "
            "levels of stress and mentioned difficulty sleeping. His productivity has actually declined "
            "despite the long hours. He is considering taking a leave of absence if the situation doesn't "
            "improve. He feels the team is understaffed and has been vocal about needing additional hires. "
            "Tom also mentioned he's been getting headaches and his doctor recommended reducing work stress."
        ),
        'summary': (
            "Key Points:\n• Working 60+ hours/week for past month\n"
            "• High stress, difficulty sleeping, declining productivity\n"
            "• Considering leave of absence\n"
            "• Team understaffed, needs additional hires\n"
            "• Health concerns: headaches, doctor recommends reduced stress"
        ),
        'sentiment': 0.18,
        'topics': [
            {'topic': 'Work-Life Balance', 'relevance': 0.95},
            {'topic': 'Feedback', 'relevance': 0.7},
            {'topic': 'Team Dynamics', 'relevance': 0.4},
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed the database with demo employees, meetings, and insights'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')

        employees_data = [
            {'name': 'Sarah Chen', 'role': 'Senior Engineer', 'department': 'Engineering', 'manager': 'Alex Rivera', 'email': 'sarah.chen@teamsense.ai'},
            {'name': 'James Wilson', 'role': 'Data Scientist', 'department': 'Data Science', 'manager': 'Lisa Patel', 'email': 'james.wilson@teamsense.ai'},
            {'name': 'Priya Sharma', 'role': 'Staff Engineer', 'department': 'Engineering', 'manager': 'Alex Rivera', 'email': 'priya.sharma@teamsense.ai'},
            {'name': 'Michael Torres', 'role': 'Engineering Manager', 'department': 'Engineering', 'manager': 'CTO', 'email': 'michael.torres@teamsense.ai'},
            {'name': 'Elena Volkov', 'role': 'Junior Developer', 'department': 'Engineering', 'manager': 'Michael Torres', 'email': 'elena.volkov@teamsense.ai'},
            {'name': 'David Okafor', 'role': 'Sales Engineer', 'department': 'Sales', 'manager': 'Jen Park', 'email': 'david.okafor@teamsense.ai'},
            {'name': 'Aisha Rahman', 'role': 'Team Lead', 'department': 'Mobile', 'manager': 'Alex Rivera', 'email': 'aisha.rahman@teamsense.ai'},
            {'name': 'Tom Bradley', 'role': 'Backend Developer', 'department': 'Engineering', 'manager': 'Michael Torres', 'email': 'tom.bradley@teamsense.ai'},
        ]

        today = date.today()
        employees = []

        for i, emp_data in enumerate(employees_data):
            employee, created = Employee.objects.get_or_create(
                email=emp_data['email'],
                defaults={
                    'name': emp_data['name'],
                    'role': emp_data['role'],
                    'department': emp_data['department'],
                    'manager': emp_data['manager'],
                    'join_date': today - timedelta(days=random.randint(90, 1200)),
                },
            )
            employees.append(employee)
            status = 'Created' if created else 'Already exists'
            self.stdout.write(f'  {status}: {employee.name}')

        # Create meetings only for employees without any existing meeting records.
        # This prevents startup from adding more random rows on every container run.
        for i, emp in enumerate(employees):
            if i < len(SAMPLE_TRANSCRIPTS):
                if Meeting.objects.filter(employee=emp).exists():
                    continue
                sample = SAMPLE_TRANSCRIPTS[i]
                meeting, created = Meeting.objects.get_or_create(
                    employee=emp,
                    date=today - timedelta(days=random.randint(1, 30)),
                    defaults={
                        'transcript': sample['transcript'],
                        'summary': sample['summary'],
                        'sentiment_score': sample['sentiment'],
                        'key_topics': sample['topics'],
                    },
                )
                if created:
                    self.stdout.write(f'  Created meeting for {emp.name}')

                    # Create insights
                    EmployeeInsight.objects.update_or_create(
                        employee=emp,
                        defaults={
                            'topics': sample['topics'],
                            'career_goals': 'Grow into leadership role' if sample['sentiment'] > 0.6 else 'Improve work conditions',
                            'concerns': '' if sample['sentiment'] > 0.6 else 'Workload and growth concerns',
                            'burnout_risk': round(max(0, 1.0 - sample['sentiment']), 2),
                        },
                    )

        self.stdout.write(self.style.SUCCESS(f'Seeding complete! {len(employees)} employees, {Meeting.objects.count()} meetings.'))
