import io
import logging
import os
import re
import uuid
from datetime import datetime

import pandas as pd
from celery import shared_task
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction
from django.utils import timezone

from ai_engine.sentiment import analyze_sentiment, get_emotion_breakdown
from ai_engine.summarizer import summarize_transcript
from ai_services.emotion_service import EmotionService
from analytics.models import SentimentInsight
from employees.models import Employee
from meetings.models import Meeting, MeetingParticipant

from .models import Document, Feedback, IngestionJob

logger = logging.getLogger(__name__)
_EMOTION_SERVICE = None


def _get_emotion_service():
    global _EMOTION_SERVICE
    if _EMOTION_SERVICE is None:
        _EMOTION_SERVICE = EmotionService()
    return _EMOTION_SERVICE


def _maybe_fetch_slack_messages(channel):
    token = getattr(settings, 'SLACK_BOT_TOKEN', '')
    if not token:
        return []
    try:
        from slack_sdk import WebClient

        client = WebClient(token=token)
        response = client.conversations_history(channel=channel, limit=100)
        messages = response.get('messages', [])
        normalized = []
        for message in messages:
            normalized.append(
                {
                    'text': message.get('text', ''),
                    'timestamp': message.get('ts'),
                    'user_name': message.get('user'),
                }
            )
        return normalized
    except Exception as exc:
        logger.warning('Slack auto-fetch failed: %s', exc)
        return []


def _maybe_fetch_google_forms(form_id):
    service_account = getattr(settings, 'GOOGLE_SERVICE_ACCOUNT', '')
    if not service_account or not form_id:
        return []
    try:
        import gspread

        client = gspread.service_account(filename=service_account)
        sheet = client.open_by_key(form_id).sheet1
        rows = sheet.get_all_records()
        normalized = []
        for row in rows:
            normalized.append(
                {
                    'employee_email': row.get('Email') or row.get('email'),
                    'name': row.get('Name') or row.get('name'),
                    'feedback': row.get('Feedback') or row.get('feedback') or row.get('Response') or '',
                    'timestamp': row.get('Timestamp') or row.get('timestamp'),
                    'department': row.get('Department') or row.get('department'),
                    'manager': row.get('Manager') or row.get('manager'),
                }
            )
        return normalized
    except Exception as exc:
        logger.warning('Google Forms auto-fetch failed: %s', exc)
        return []


def _to_datetime(value):
    if value is None or value == '':
        return timezone.now()
    if isinstance(value, datetime):
        return timezone.make_aware(value) if timezone.is_naive(value) else value
    parsed = pd.to_datetime(value, errors='coerce')
    if pd.isna(parsed):
        return timezone.now()
    py_dt = parsed.to_pydatetime()
    return timezone.make_aware(py_dt) if timezone.is_naive(py_dt) else py_dt


def _to_date(value):
    dt = _to_datetime(value)
    return dt.date()


def _safe_text(value):
    if value is None:
        return ''
    return str(value).strip()


def _placeholder_email(seed):
    cleaned = re.sub(r'[^a-zA-Z0-9]+', '', str(seed).lower()) or uuid.uuid4().hex[:8]
    return f"{cleaned}@placeholder.local"


def _upsert_employee(payload):
    employee_id = payload.get('employee_id')
    email = _safe_text(payload.get('email'))
    name = _safe_text(payload.get('name')) or 'Unknown Employee'
    department = _safe_text(payload.get('department')) or 'General'
    manager = _safe_text(payload.get('manager'))
    role = _safe_text(payload.get('role')) or 'Employee'
    join_date = _to_date(payload.get('join_date'))

    employee = None
    if employee_id:
        try:
            employee = Employee.objects.filter(id=int(employee_id)).first()
        except (TypeError, ValueError):
            employee = None

    if employee is None and email:
        employee = Employee.objects.filter(email=email).first()

    if employee is None:
        create_email = email or _placeholder_email(employee_id or name)
        suffix = 1
        base_email = create_email
        while Employee.objects.filter(email=create_email).exists():
            create_email = f"{base_email.split('@')[0]}{suffix}@{base_email.split('@')[1]}"
            suffix += 1

        employee = Employee.objects.create(
            name=name,
            role=role,
            department=department,
            manager=manager,
            join_date=join_date,
            email=create_email,
        )
    else:
        updates = []
        if name and employee.name != name:
            employee.name = name
            updates.append('name')
        if department and employee.department != department:
            employee.department = department
            updates.append('department')
        if manager and employee.manager != manager:
            employee.manager = manager
            updates.append('manager')
        if role and employee.role != role:
            employee.role = role
            updates.append('role')
        if email and employee.email != email and not Employee.objects.filter(email=email).exclude(id=employee.id).exists():
            employee.email = email
            updates.append('email')
        if updates:
            employee.save(update_fields=updates + ['updated_at'])

    return employee


def _create_sentiment_insight(employee, source_type, score, text):
    emotion_distribution = _get_emotion_service().analyze(text or '')
    SentimentInsight.objects.create(
        employee=employee,
        source_type=source_type,
        sentiment_score=score,
        insights={
            'emotion_breakdown': get_emotion_breakdown(text),
            'transformer_emotions': emotion_distribution,
            'length': len(text),
        },
        timestamp=timezone.now(),
    )


@shared_task(bind=True)
def parse_csv_task(self, storage_path, user_id=None, job_id=None):
    records = 0
    try:
        if job_id:
            IngestionJob.objects.filter(id=job_id).update(
                status=IngestionJob.STATUS_PROCESSING,
                started_at=timezone.now(),
            )

        with default_storage.open(storage_path, 'rb') as handle:
            file_bytes = handle.read()

        file_ext = os.path.splitext(storage_path)[1].lower()
        if file_ext in ('.xlsx', '.xls'):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            df = pd.read_csv(io.BytesIO(file_bytes))

        with transaction.atomic():
            for _, row in df.iterrows():
                row_data = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
                payload = {
                    'employee_id': row_data.get('employee_id') or row_data.get('id'),
                    'name': row_data.get('name') or row_data.get('employee_name'),
                    'email': row_data.get('email'),
                    'department': row_data.get('department'),
                    'manager': row_data.get('manager'),
                    'role': row_data.get('role'),
                    'join_date': row_data.get('join_date') or row_data.get('date_of_joining'),
                }
                employee = _upsert_employee(payload)

                content = _safe_text(
                    row_data.get('feedback')
                    or row_data.get('comment')
                    or row_data.get('message')
                    or row_data.get('notes')
                )
                if not content:
                    content = f"Employee profile ingested from CSV/Excel for {employee.name}."

                sentiment = analyze_sentiment(content)
                timestamp = _to_datetime(row_data.get('timestamp'))

                Feedback.objects.create(
                    employee=employee,
                    source=Feedback.SOURCE_CSV,
                    content=content,
                    sentiment=sentiment,
                    timestamp=timestamp,
                    raw_data=row_data,
                )
                _create_sentiment_insight(employee, 'feedback', sentiment, content)
                records += 1

        default_storage.delete(storage_path)
        if job_id:
            IngestionJob.objects.filter(id=job_id).update(
                status=IngestionJob.STATUS_COMPLETED,
                records_processed=records,
                completed_at=timezone.now(),
            )
    except Exception as exc:
        logger.exception('CSV/Excel ingestion failed: %s', exc)
        if job_id:
            IngestionJob.objects.filter(id=job_id).update(
                status=IngestionJob.STATUS_FAILED,
                error_message=str(exc),
                completed_at=timezone.now(),
            )
        raise


@shared_task(bind=True)
def ingest_slack_messages_task(self, messages, channel='hr-feedback', user_id=None, job_id=None):
    records = 0
    try:
        if job_id:
            IngestionJob.objects.filter(id=job_id).update(
                status=IngestionJob.STATUS_PROCESSING,
                started_at=timezone.now(),
            )

        source_messages = messages or _maybe_fetch_slack_messages(channel)
        for message in source_messages:
            text = _safe_text(message.get('text'))
            if not text:
                continue

            payload = {
                'employee_id': message.get('employee_id'),
                'name': message.get('employee_name') or message.get('name') or message.get('user_name'),
                'email': message.get('employee_email') or message.get('email'),
                'department': message.get('department'),
                'manager': message.get('manager'),
                'join_date': message.get('join_date'),
            }
            employee = _upsert_employee(payload)
            sentiment = analyze_sentiment(text)

            Feedback.objects.create(
                employee=employee,
                source=Feedback.SOURCE_SLACK,
                content=text,
                sentiment=sentiment,
                timestamp=_to_datetime(message.get('timestamp') or message.get('ts')),
                raw_data={'channel': channel, **message},
            )
            _create_sentiment_insight(employee, 'feedback', sentiment, text)
            records += 1

        if job_id:
            IngestionJob.objects.filter(id=job_id).update(
                status=IngestionJob.STATUS_COMPLETED,
                records_processed=records,
                completed_at=timezone.now(),
            )
    except Exception as exc:
        logger.exception('Slack ingestion failed: %s', exc)
        if job_id:
            IngestionJob.objects.filter(id=job_id).update(
                status=IngestionJob.STATUS_FAILED,
                error_message=str(exc),
                completed_at=timezone.now(),
            )
        raise


@shared_task(bind=True)
def ingest_google_forms_task(self, responses, form_id='', user_id=None, job_id=None):
    records = 0
    try:
        if job_id:
            IngestionJob.objects.filter(id=job_id).update(
                status=IngestionJob.STATUS_PROCESSING,
                started_at=timezone.now(),
            )

        source_responses = responses or _maybe_fetch_google_forms(form_id)
        for response in source_responses:
            feedback_text = _safe_text(response.get('feedback') or response.get('response') or response.get('comment'))
            payload = {
                'employee_id': response.get('employee_id'),
                'name': response.get('name') or response.get('employee_name'),
                'email': response.get('email') or response.get('employee_email'),
                'department': response.get('department'),
                'manager': response.get('manager'),
                'join_date': response.get('join_date'),
            }
            employee = _upsert_employee(payload)

            sentiment = analyze_sentiment(feedback_text or f"Google Forms response for {employee.name}")
            Feedback.objects.create(
                employee=employee,
                source=Feedback.SOURCE_FORMS,
                content=feedback_text or 'No textual feedback provided.',
                sentiment=sentiment,
                timestamp=_to_datetime(response.get('timestamp')),
                raw_data={'form_id': form_id, **response},
            )
            _create_sentiment_insight(employee, 'feedback', sentiment, feedback_text or '')
            records += 1

        if job_id:
            IngestionJob.objects.filter(id=job_id).update(
                status=IngestionJob.STATUS_COMPLETED,
                records_processed=records,
                completed_at=timezone.now(),
            )
    except Exception as exc:
        logger.exception('Google Forms ingestion failed: %s', exc)
        if job_id:
            IngestionJob.objects.filter(id=job_id).update(
                status=IngestionJob.STATUS_FAILED,
                error_message=str(exc),
                completed_at=timezone.now(),
            )
        raise


def _extract_text_from_document(storage_path):
    ext = os.path.splitext(storage_path)[1].lower()
    with default_storage.open(storage_path, 'rb') as handle:
        file_bytes = handle.read()

    if ext in ('.txt', '.md'):
        return file_bytes.decode('utf-8', errors='ignore')

    if ext == '.pdf':
        try:
            import fitz
            text_parts = []
            with fitz.open(stream=file_bytes, filetype='pdf') as doc:
                for page in doc:
                    text_parts.append(page.get_text())
            return '\n'.join(text_parts).strip()
        except Exception:
            return file_bytes.decode('utf-8', errors='ignore')

    return file_bytes.decode('utf-8', errors='ignore')


@shared_task(bind=True)
def ingest_document_task(self, storage_path, file_name, participants=None, employee_id=None, user_id=None, job_id=None):
    records = 0
    try:
        if job_id:
            IngestionJob.objects.filter(id=job_id).update(
                status=IngestionJob.STATUS_PROCESSING,
                started_at=timezone.now(),
            )

        content = _extract_text_from_document(storage_path)
        summary = summarize_transcript(content[:6000]) if content else 'No extractable text found.'
        sentiment = analyze_sentiment(content or summary)

        linked_employee = None
        if employee_id:
            linked_employee = Employee.objects.filter(id=employee_id).first()

        document = Document.objects.create(
            employee=linked_employee,
            file_name=file_name,
            content=content,
            summary=summary,
            sentiment=sentiment,
            raw_data={'participants': participants or []},
        )

        participant_employees = []
        for participant in participants or []:
            participant_employees.append(
                _upsert_employee({'name': participant, 'department': 'General', 'join_date': timezone.now().date()})
            )

        if linked_employee and linked_employee not in participant_employees:
            participant_employees.append(linked_employee)

        primary_employee = participant_employees[0] if participant_employees else linked_employee
        if primary_employee is None:
            primary_employee = _upsert_employee({'name': 'Document Participant', 'department': 'General', 'join_date': timezone.now().date()})

        if primary_employee:
            meeting = Meeting.objects.create(
                employee=primary_employee,
                date=timezone.now().date(),
                transcript=content[:12000],
                summary=summary,
                sentiment_score=sentiment,
                key_topics=[],
                meeting_title=f"Ingested Note: {file_name[:80]}",
                meeting_date=timezone.now().date(),
            )
            for participant_employee in participant_employees:
                MeetingParticipant.objects.get_or_create(meeting=meeting, employee=participant_employee)
                _create_sentiment_insight(participant_employee, 'doc', sentiment, summary)
            records += 1

        default_storage.delete(storage_path)

        if job_id:
            IngestionJob.objects.filter(id=job_id).update(
                status=IngestionJob.STATUS_COMPLETED,
                records_processed=records,
                completed_at=timezone.now(),
                metadata={'document_id': document.id},
            )
    except Exception as exc:
        logger.exception('Document ingestion failed: %s', exc)
        if job_id:
            IngestionJob.objects.filter(id=job_id).update(
                status=IngestionJob.STATUS_FAILED,
                error_message=str(exc),
                completed_at=timezone.now(),
            )
        raise
