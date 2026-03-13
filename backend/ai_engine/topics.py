"""Topic extraction from meeting transcripts."""
import re
import logging

logger = logging.getLogger(__name__)

# Topic categories and their keywords
TOPIC_CATEGORIES = {
    'Career Development': ['career', 'promotion', 'growth', 'learning', 'training', 'skills', 'development', 'mentoring'],
    'Performance': ['performance', 'review', 'goals', 'objectives', 'kpi', 'metrics', 'productivity', 'achievement'],
    'Work-Life Balance': ['balance', 'workload', 'overtime', 'burnout', 'stress', 'health', 'wellness', 'vacation'],
    'Team Dynamics': ['team', 'collaboration', 'conflict', 'communication', 'culture', 'teamwork', 'morale'],
    'Project Updates': ['project', 'deadline', 'milestone', 'deliverable', 'sprint', 'release', 'launch'],
    'Compensation': ['salary', 'compensation', 'benefits', 'raise', 'bonus', 'equity', 'pay'],
    'Feedback': ['feedback', 'improvement', 'suggestion', 'concern', 'issue', 'complaint'],
    'Innovation': ['innovation', 'idea', 'research', 'experiment', 'proposal', 'initiative'],
}


def extract_topics(transcript: str) -> list:
    """Extract topics from a meeting transcript using keyword matching."""
    text_lower = transcript.lower()
    topics_found = []

    for topic, keywords in TOPIC_CATEGORIES.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches >= 2:
            topics_found.append({'topic': topic, 'relevance': min(matches / len(keywords), 1.0)})

    # Sort by relevance
    topics_found.sort(key=lambda x: x['relevance'], reverse=True)
    return topics_found


def extract_career_goals(transcript: str) -> str:
    """Extract career goals mentioned in a transcript."""
    goal_patterns = [
        r'(?:goal|objective|aspiration|ambition|plan)s?\s*(?:is|are|include)?\s*[:.]?\s*(.{20,200})',
        r'(?:want|hope|plan|aim|intend)\s+to\s+(.{20,150})',
        r'(?:career|professional)\s+(?:goal|path|direction)\s*[:.]?\s*(.{20,200})',
    ]

    goals = []
    for pattern in goal_patterns:
        matches = re.findall(pattern, transcript, re.IGNORECASE)
        goals.extend(matches[:2])

    if goals:
        return '; '.join(set(goals[:3]))
    return ''


def extract_concerns(transcript: str) -> str:
    """Extract concerns or issues mentioned in a transcript."""
    concern_patterns = [
        r'(?:concern|worried|issue|problem|challenge|difficulty|struggle)s?\s*(?:is|are|about|with|regarding)?\s*[:.]?\s*(.{20,200})',
        r'(?:frustrated|overwhelmed|stressed|unhappy)\s+(?:about|with|by)\s+(.{20,150})',
    ]

    concerns = []
    for pattern in concern_patterns:
        matches = re.findall(pattern, transcript, re.IGNORECASE)
        concerns.extend(matches[:2])

    if concerns:
        return '; '.join(set(concerns[:3]))
    return ''


def update_employee_insights(employee_id: int):
    """Update the EmployeeInsight record for an employee based on all their meetings."""
    from meetings.models import Meeting
    from analytics.models import EmployeeInsight
    from employees.models import Employee
    from .sentiment import analyze_sentiment

    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        logger.error(f"Employee {employee_id} not found")
        return

    meetings = Meeting.objects.filter(employee=employee).order_by('-date')

    if not meetings.exists():
        return

    # Aggregate topics from all meetings
    all_topics = {}
    all_goals = []
    all_concerns = []
    sentiment_scores = []

    for meeting in meetings:
        topics = extract_topics(meeting.transcript)
        for t in topics:
            name = t['topic']
            all_topics[name] = all_topics.get(name, 0) + t['relevance']

        goals = extract_career_goals(meeting.transcript)
        if goals:
            all_goals.append(goals)

        concerns = extract_concerns(meeting.transcript)
        if concerns:
            all_concerns.append(concerns)

        if meeting.sentiment_score is not None:
            sentiment_scores.append(meeting.sentiment_score)

    # Calculate burnout risk based on sentiment trend and concern frequency
    burnout_risk = 0.0
    if sentiment_scores:
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        # Lower sentiment → higher burnout risk
        burnout_risk = max(0.0, 1.0 - avg_sentiment)

    # Adjust for number of concerns
    concern_factor = min(len(all_concerns) * 0.1, 0.3)
    burnout_risk = min(burnout_risk + concern_factor, 1.0)

    # Build sorted topic list
    sorted_topics = sorted(all_topics.items(), key=lambda x: x[1], reverse=True)
    topic_list = [{'topic': t[0], 'weight': round(t[1], 2)} for t in sorted_topics[:8]]

    # Update or create insight
    EmployeeInsight.objects.update_or_create(
        employee=employee,
        defaults={
            'topics': topic_list,
            'career_goals': '; '.join(all_goals[:3]) if all_goals else '',
            'concerns': '; '.join(all_concerns[:3]) if all_concerns else '',
            'burnout_risk': round(burnout_risk, 3),
        },
    )

    logger.info(f"Updated insights for employee {employee.name}")
