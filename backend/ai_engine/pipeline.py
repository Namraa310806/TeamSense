"""Main AI processing pipeline. Orchestrates all AI tasks for a meeting transcript."""
import logging

logger = logging.getLogger(__name__)


def run_pipeline(meeting_id: int):
    """Run the full AI pipeline for a meeting transcript.

    Steps:
    1. Clean transcript
    2. Summarize transcript
    3. Analyze sentiment
    4. Extract topics
    5. Generate and store embedding
    6. Update employee insights
    """
    from meetings.models import Meeting
    from .summarizer import summarize_transcript
    from .sentiment import analyze_sentiment
    from .embeddings import generate_and_store_embedding
    from .topics import extract_topics, update_employee_insights

    try:
        meeting = Meeting.objects.get(id=meeting_id)
    except Meeting.DoesNotExist:
        logger.error(f"Meeting {meeting_id} not found")
        return

    logger.info(f"Starting AI pipeline for meeting {meeting_id}")

    # Step 1 & 2: Summarize transcript
    try:
        summary = summarize_transcript(meeting.transcript)
        meeting.summary = summary
        logger.info(f"Summary generated for meeting {meeting_id}")
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        meeting.summary = "Summary generation failed."

    # Step 3: Analyze sentiment
    try:
        sentiment = analyze_sentiment(meeting.transcript)
        meeting.sentiment_score = sentiment
        logger.info(f"Sentiment score for meeting {meeting_id}: {sentiment}")
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        meeting.sentiment_score = 0.5

    # Step 4: Extract topics
    try:
        topics = extract_topics(meeting.transcript)
        meeting.key_topics = topics
        logger.info(f"Topics extracted for meeting {meeting_id}: {[t['topic'] for t in topics]}")
    except Exception as e:
        logger.error(f"Topic extraction failed: {e}")
        meeting.key_topics = []

    meeting.save()

    # Step 5: Generate and store embedding
    try:
        generate_and_store_embedding(meeting)
        logger.info(f"Embedding stored for meeting {meeting_id}")
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")

    # Step 6: Update employee insights
    try:
        update_employee_insights(meeting.employee_id)
        logger.info(f"Insights updated for employee {meeting.employee_id}")
    except Exception as e:
        logger.error(f"Insight update failed: {e}")

    logger.info(f"AI pipeline completed for meeting {meeting_id}")
