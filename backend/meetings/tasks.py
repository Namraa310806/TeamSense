from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(name='meetings.process_transcript')
def process_transcript_task(meeting_id):
    """Main pipeline task - processes transcript through all AI stages."""
    logger.info(f"Processing transcript for meeting {meeting_id}")
    from ai_engine.pipeline import run_pipeline
    run_pipeline(meeting_id)
    logger.info(f"Pipeline completed for meeting {meeting_id}")


@shared_task(name='meetings.generate_embeddings')
def generate_embeddings_task(meeting_id):
    """Generate and store embeddings for a meeting transcript."""
    logger.info(f"Generating embeddings for meeting {meeting_id}")
    from ai_engine.embeddings import generate_and_store_embedding
    from meetings.models import Meeting
    meeting = Meeting.objects.get(id=meeting_id)
    generate_and_store_embedding(meeting)


@shared_task(name='meetings.calculate_sentiment')
def calculate_sentiment_task(meeting_id):
    """Calculate sentiment score for a meeting transcript."""
    logger.info(f"Calculating sentiment for meeting {meeting_id}")
    from ai_engine.sentiment import analyze_sentiment
    from meetings.models import Meeting
    meeting = Meeting.objects.get(id=meeting_id)
    score = analyze_sentiment(meeting.transcript)
    meeting.sentiment_score = score
    meeting.save()


@shared_task(name='meetings.update_insights')
def update_insights_task(employee_id):
    """Update AI insights for an employee based on all meetings."""
    logger.info(f"Updating insights for employee {employee_id}")
    from ai_engine.topics import update_employee_insights
    update_employee_insights(employee_id)


@shared_task(name='meetings.update_attrition')
def update_attrition_task(employee_id):
    """Recalculate attrition risk for employee after sentiment update."""
    logger.info(f"Updating attrition risk for employee {employee_id}")
    from ai_engine.attrition import calculate_attrition_risk
    # Optional: Cache result in EmployeeInsight or log
    risk_data = calculate_attrition_risk(employee_id)
    logger.info(f"Attrition risk updated: {risk_data}")
