"""Attrition risk prediction using rule-based heuristics."""
import logging
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


def calculate_attrition_risk(employee_id: int) -> dict:
    """Calculate attrition risk score for an employee.

    Uses a rule-based approach based on:
    - Sentiment trends (declining sentiment)
    - Concern/complaint frequency
    - Meeting engagement (frequency of meetings)
    - Burnout risk from insights

    Returns:
        dict with risk_score (0-1), risk_level, and contributing factors
    """
    from meetings.models import Meeting
    from analytics.models import EmployeeInsight
    from employees.models import Employee

    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return {'risk_score': 0.0, 'risk_level': 'unknown', 'factors': []}

    meetings = Meeting.objects.filter(employee=employee).order_by('-date')
    factors = []
    risk_score = 0.0

    if not meetings.exists():
        return {
            'risk_score': 0.1,
            'risk_level': 'low',
            'factors': ['No meeting data available for assessment'],
        }

    # Factor 1: Average sentiment (weight: 0.3)
    sentiment_scores = [m.sentiment_score for m in meetings if m.sentiment_score is not None]
    if sentiment_scores:
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        sentiment_risk = max(0, (0.5 - avg_sentiment) * 2)  # Below 0.5 → risk
        risk_score += sentiment_risk * 0.3
        if avg_sentiment < 0.4:
            factors.append(f'Low average sentiment ({avg_sentiment:.2f})')

    # Factor 2: Sentiment trend (weight: 0.25)
    if len(sentiment_scores) >= 3:
        recent = sentiment_scores[:3]
        older = sentiment_scores[3:6] if len(sentiment_scores) > 3 else sentiment_scores[:3]
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        if recent_avg < older_avg:
            decline = older_avg - recent_avg
            risk_score += min(decline * 2, 1.0) * 0.25
            if decline > 0.1:
                factors.append(f'Declining sentiment trend (-{decline:.2f})')

    # Factor 3: Concern frequency (weight: 0.2)
    concern_keywords = ['concern', 'frustrated', 'unhappy', 'leaving', 'quit', 'resign',
                        'burnout', 'overwhelmed', 'undervalued', 'unfair']
    concern_count = 0
    for meeting in meetings:
        text_lower = meeting.transcript.lower()
        concern_count += sum(1 for kw in concern_keywords if kw in text_lower)

    if concern_count > 0:
        concern_risk = min(concern_count * 0.15, 1.0)
        risk_score += concern_risk * 0.2
        if concern_count >= 3:
            factors.append(f'Multiple concerns raised ({concern_count} mentions)')

    # Factor 4: Meeting recency (weight: 0.1)
    last_meeting = meetings.first()
    if last_meeting:
        days_since = (timezone.now().date() - last_meeting.date).days
        if days_since > 60:
            risk_score += 0.1
            factors.append(f'No recent meetings ({days_since} days ago)')

    # Factor 5: Burnout risk from insights (weight: 0.15)
    try:
        insight = EmployeeInsight.objects.get(employee=employee)
        if insight.burnout_risk > 0.5:
            risk_score += insight.burnout_risk * 0.15
            factors.append(f'Elevated burnout risk ({insight.burnout_risk:.2f})')
    except EmployeeInsight.DoesNotExist:
        pass

    # Clamp and categorize
    risk_score = round(min(max(risk_score, 0.0), 1.0), 3)

    if risk_score >= 0.7:
        risk_level = 'critical'
    elif risk_score >= 0.5:
        risk_level = 'high'
    elif risk_score >= 0.3:
        risk_level = 'medium'
    else:
        risk_level = 'low'

    if not factors:
        factors.append('No significant risk factors detected')

    return {
        'risk_score': risk_score,
        'risk_level': risk_level,
        'factors': factors,
    }
