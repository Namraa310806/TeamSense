import logging

logger = logging.getLogger(__name__)


def schedule_uploaded_meeting_pipeline(meeting_id: int) -> str:
    """Queue uploaded meeting processing; fallback to synchronous execution."""
    try:
        from meetings.tasks import process_uploaded_meeting_task

        process_uploaded_meeting_task.delay(meeting_id)
        return 'queued'
    except Exception as exc:
        logger.warning('Celery queue failed for meeting %s: %s. Running sync fallback.', meeting_id, exc)
        from meetings.analysis_pipeline import run_meeting_intelligence_pipeline

        run_meeting_intelligence_pipeline(meeting_id)
        return 'completed'


def schedule_text_meeting_pipeline(meeting_id: int) -> str:
    """Queue transcript-only processing; fallback to synchronous execution."""
    try:
        from meetings.tasks import process_transcript_task

        process_transcript_task.delay(meeting_id)
        return 'queued'
    except Exception as exc:
        logger.warning('Celery transcript queue failed for meeting %s: %s. Running sync fallback.', meeting_id, exc)
        from meetings.analysis_pipeline import run_text_meeting_intelligence_pipeline

        run_text_meeting_intelligence_pipeline(meeting_id)
        return 'completed'
