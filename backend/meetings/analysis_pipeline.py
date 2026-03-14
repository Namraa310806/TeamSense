import json
import logging
import os
import re
import subprocess
import tempfile
from collections import Counter, defaultdict

import numpy as np
from django.utils import timezone
from ai_engine.model_loader import ModelManager

from analytics.models import MeetingAnalysis
from ai_services.sentiment_service import SentimentService
from ai_services.summarization_service import SummarizationService
from meetings.models import (
    EmployeeMeetingInsight,
    Meeting,
    MeetingInsight,
    MeetingParticipant,
    MeetingSpeakerMapping,
    MeetingTranscript,
)

logger = logging.getLogger(__name__)

_ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.mp4', '.m4a'}
_ASR_PIPELINE = None
_SENTIMENT_SERVICE = None
_SUMMARY_SERVICE = None


def _get_asr_pipeline():
    global _ASR_PIPELINE
    if _ASR_PIPELINE is None:
        _ASR_PIPELINE = ModelManager.get_whisper_pipeline()
    return _ASR_PIPELINE


def _get_sentiment_service():
    global _SENTIMENT_SERVICE
    if _SENTIMENT_SERVICE is None:
        _SENTIMENT_SERVICE = SentimentService()
    return _SENTIMENT_SERVICE


def _get_summary_service():
    global _SUMMARY_SERVICE
    if _SUMMARY_SERVICE is None:
        _SUMMARY_SERVICE = SummarizationService()
    return _SUMMARY_SERVICE


def validate_media_extension(filename: str):
    _, ext = os.path.splitext(filename.lower())
    if ext not in _ALLOWED_EXTENSIONS:
        raise ValueError('Unsupported format. Allowed: mp3, wav, mp4, m4a')


def _convert_to_wav(input_path: str) -> str:
    fd, output_path = tempfile.mkstemp(suffix='.wav')
    os.close(fd)
    cmd = [
        'ffmpeg',
        '-y',
        '-i',
        input_path,
        '-ac',
        '1',
        '-ar',
        '16000',
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f'ffmpeg conversion failed: {result.stderr[:400]}')
    return output_path


def _to_hh_mm_ss(seconds: float) -> str:
    value = max(float(seconds), 0.0)
    hours = int(value // 3600)
    mins = int(value // 60)
    secs = int(value % 60)
    return f"{hours:02d}:{mins % 60:02d}:{secs:02d}"


def _extract_timestamped_segments(asr_result):
    chunks = asr_result.get('chunks') or []
    segments = []
    for item in chunks:
        if not isinstance(item, dict):
            continue
        text = str(item.get('text', '')).strip()
        ts = item.get('timestamp') or (0.0, 0.0)
        start = float(ts[0] or 0.0)
        end = float(ts[1] or start)
        if text:
            segments.append(
                {
                    'text': text,
                    'start': start,
                    'end': end,
                }
            )

    if not segments and asr_result.get('text'):
        text = str(asr_result.get('text', '')).strip()
        if text:
            segments.append({'text': text, 'start': 0.0, 'end': 0.0})

    return segments


def _asr_transcribe_with_timestamps(wav_path: str):
    asr = _get_asr_pipeline()
    try:
        result = asr(wav_path, return_timestamps=True)
    except Exception:
        # Retry once with a fresh pipeline instance.
        global _ASR_PIPELINE
        _ASR_PIPELINE = None
        asr = _get_asr_pipeline()
        result = asr(wav_path, return_timestamps=True)
    return _extract_timestamped_segments(result)


def _diarize_segments(segments, speaker_count=2):
    if not segments:
        return []

    unique_count = max(1, int(speaker_count or 1))
    diarized = []

    # Lightweight diarization fallback: assign stable speaker labels across turns.
    for index, segment in enumerate(segments):
        speaker_idx = (index % unique_count) + 1
        diarized.append(
            {
                'speaker': f'Speaker_{speaker_idx}',
                'text': segment['text'],
                'start': float(segment['start']),
                'end': float(segment['end']),
            }
        )

    return diarized


def transcribe_recording(uploaded_file):
    validate_media_extension(uploaded_file.name)

    fd, temp_input = tempfile.mkstemp(suffix=os.path.splitext(uploaded_file.name)[1].lower())
    os.close(fd)
    temp_wav = None

    try:
        with open(temp_input, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        temp_wav = _convert_to_wav(temp_input)
        try:
            segments = _asr_transcribe_with_timestamps(temp_wav)
            transcript = ' '.join(s['text'] for s in segments).strip()
        except Exception as exc:
            logger.exception('Whisper transcription failed for %s: %s', uploaded_file.name, exc)
            segments = []
            transcript = 'Transcription unavailable due to model/runtime error. Audio was received successfully.'
        return {
            'transcript': transcript,
            'segments': segments,
        }
    finally:
        if os.path.exists(temp_input):
            os.remove(temp_input)
        if temp_wav and os.path.exists(temp_wav):
            os.remove(temp_wav)


def parse_speaker_turns(raw_turns):
    if not raw_turns:
        return []

    if isinstance(raw_turns, str):
        raw_turns = raw_turns.strip()
        if not raw_turns:
            return []
        try:
            parsed = json.loads(raw_turns)
        except json.JSONDecodeError as exc:
            raise ValueError(f'Invalid speaker_turns JSON: {exc}')
        raw_turns = parsed

    if not isinstance(raw_turns, list):
        raise ValueError('speaker_turns must be a JSON array')

    normalized = []
    for item in raw_turns:
        if not isinstance(item, dict):
            continue
        speaker = str(item.get('speaker', '')).strip()
        text = str(item.get('text', '')).strip()
        start = float(item.get('start_time', 0.0) or 0.0)
        end = float(item.get('end_time', start) or start)
        employee_id = item.get('employee_id')
        if speaker and text:
            normalized.append(
                {
                    'speaker': speaker,
                    'employee_id': employee_id,
                    'text': text,
                    'start': start,
                    'end': end,
                }
            )
    return normalized


def _build_name_based_turns(transcript, employees, segments=None):
    if not transcript or not employees:
        return []

    if segments:
        chunks = segments
    else:
        text_chunks = [c.strip() for c in re.split(r'(?<=[.!?])\s+|\n+', transcript) if c.strip()]
        chunks = [{'text': c, 'start': float(i * 10), 'end': float((i + 1) * 10)} for i, c in enumerate(text_chunks)]
        if not chunks:
            chunks = [{'text': transcript.strip(), 'start': 0.0, 'end': 0.0}]

    patterns = []
    for emp in employees:
        full = re.escape(emp.name.lower())
        first = re.escape(emp.name.split()[0].lower()) if emp.name else ''
        patterns.append((emp, [rf'\b{full}\b', rf'\b{first}\b'] if first else [rf'\b{full}\b']))

    turns = []
    fallback_idx = 0
    for chunk in chunks:
        text = str(chunk.get('text', '')).strip()
        lowered = text.lower()
        matched_emp = None
        for emp, pats in patterns:
            if any(re.search(pat, lowered) for pat in pats):
                matched_emp = emp
                break

        if matched_emp is None:
            matched_emp = employees[fallback_idx % len(employees)]
            fallback_idx += 1

        turns.append(
            {
                'speaker': matched_emp.name,
                'employee_id': matched_emp.id,
                'text': text,
                'start': float(chunk.get('start', 0.0) or 0.0),
                'end': float(chunk.get('end', 0.0) or 0.0),
            }
        )

    return turns


def _compute_participation(speaker_turns):
    if not speaker_turns:
        return {
            'score': 0.0,
            'per_speaker': {},
            'total_words': 0,
            'per_speaker_duration': {},
            'speaking_turns': {},
            'interruption_signals': {},
        }

    word_counts = Counter()
    speaker_turn_counts = Counter()
    speaker_duration = Counter()
    speaker_interruptions = Counter()
    total_words = 0

    for turn in speaker_turns:
        words = re.findall(r"\w+", turn['text'])
        count = len(words)
        total_words += count
        word_counts[turn['speaker']] += count
        speaker_turn_counts[turn['speaker']] += 1

        duration = max(float(turn.get('end', 0.0)) - float(turn.get('start', 0.0)), 0.0)
        speaker_duration[turn['speaker']] += duration

    for idx in range(1, len(speaker_turns)):
        prev = speaker_turns[idx - 1]
        curr = speaker_turns[idx]
        if prev['speaker'] != curr['speaker']:
            gap = float(curr.get('start', 0.0)) - float(prev.get('end', 0.0))
            if gap < 0.4:
                speaker_interruptions[curr['speaker']] += 1

    if total_words == 0:
        return {
            'score': 0.0,
            'per_speaker': dict(word_counts),
            'total_words': 0,
            'per_speaker_duration': dict(speaker_duration),
            'speaking_turns': dict(speaker_turn_counts),
            'interruption_signals': dict(speaker_interruptions),
        }

    shares = [count / total_words for count in word_counts.values()]
    uniform_share = 1 / max(len(shares), 1)
    imbalance = sum(abs(s - uniform_share) for s in shares) / 2
    score = max(0.0, 1.0 - imbalance)

    return {
        'score': round(float(score), 3),
        'per_speaker': dict(word_counts),
        'total_words': total_words,
        'per_speaker_duration': dict(speaker_duration),
        'speaking_turns': dict(speaker_turn_counts),
        'interruption_signals': dict(speaker_interruptions),
    }


def _detect_signals(transcript: str):
    text = transcript.lower()

    engagement_keywords = ['idea', 'propose', 'improve', 'action item', 'next step', 'plan']
    collaboration_keywords = ['together', 'support', 'pair', 'help', 'collaborate', 'team']
    conflict_keywords = ['argue', 'conflict', 'blocked', 'frustrated', 'unfair', 'tension']

    def count_matches(keywords):
        return sum(text.count(k) for k in keywords)

    engagement_count = count_matches(engagement_keywords)
    collaboration_count = count_matches(collaboration_keywords)
    conflict_count = count_matches(conflict_keywords)

    return {
        'engagement_signals': {
            'keyword_hits': engagement_count,
            'level': 'high' if engagement_count >= 5 else 'medium' if engagement_count >= 2 else 'low',
        },
        'collaboration_signals': {
            'keyword_hits': collaboration_count,
            'level': 'high' if collaboration_count >= 5 else 'medium' if collaboration_count >= 2 else 'low',
        },
        'conflict_detection': {
            'keyword_hits': conflict_count,
            'level': 'high' if conflict_count >= 4 else 'medium' if conflict_count >= 2 else 'low',
        },
    }


def _extract_action_items(transcript: str):
    candidates = [
        line.strip()
        for line in re.split(r'\n+|(?<=[.!?])\s+', transcript)
        if line and len(line.strip()) > 16
    ]
    action_patterns = [
        r'\b(action item|next step|follow up|should|need to|let us|we will)\b',
    ]

    action_items = []
    for line in candidates:
        lowered = line.lower()
        if any(re.search(pattern, lowered) for pattern in action_patterns):
            action_items.append(line)

    deduped = []
    seen = set()
    for item in action_items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped[:5]


def _upsert_meeting_insights(meeting, summary, transcript, signals):
    MeetingInsight.objects.filter(meeting=meeting).delete()

    rows = [
        MeetingInsight(
            meeting=meeting,
            insight_type=MeetingInsight.TYPE_SUMMARY,
            description=summary or 'Summary unavailable.',
            severity=MeetingInsight.SEVERITY_LOW,
        )
    ]

    topic_tokens = []
    for topic in (meeting.key_topics or []):
        if isinstance(topic, dict):
            value = topic.get('topic')
            if value:
                topic_tokens.append(str(value))
        elif isinstance(topic, str):
            topic_tokens.append(topic)
    if topic_tokens:
        rows.append(
            MeetingInsight(
                meeting=meeting,
                insight_type=MeetingInsight.TYPE_TOPIC,
                description='Key topics: ' + ', '.join(topic_tokens[:6]),
                severity=MeetingInsight.SEVERITY_LOW,
            )
        )

    for item in _extract_action_items(transcript):
        rows.append(
            MeetingInsight(
                meeting=meeting,
                insight_type=MeetingInsight.TYPE_ACTION_ITEM,
                description=item,
                severity=MeetingInsight.SEVERITY_MEDIUM,
            )
        )

    conflict_level = signals.get('conflict_detection', {}).get('level', 'low')
    if conflict_level in ('medium', 'high'):
        severity = MeetingInsight.SEVERITY_HIGH if conflict_level == 'high' else MeetingInsight.SEVERITY_MEDIUM
        rows.append(
            MeetingInsight(
                meeting=meeting,
                insight_type=MeetingInsight.TYPE_RISK,
                description=f"Conflict risk detected: {conflict_level}.",
                severity=severity,
            )
        )

    engagement_level = signals.get('engagement_signals', {}).get('level', 'low')
    if engagement_level == 'low':
        rows.append(
            MeetingInsight(
                meeting=meeting,
                insight_type=MeetingInsight.TYPE_RISK,
                description='Low engagement signals detected in the discussion.',
                severity=MeetingInsight.SEVERITY_MEDIUM,
            )
        )

    if rows:
        MeetingInsight.objects.bulk_create(rows)


def _sentiment_by_speaker(speaker_turns, transcript):
    sentiment_service = _get_sentiment_service()

    if not speaker_turns:
        overall = sentiment_service.analyze(transcript)
        return {
            'overall': overall,
            'by_employee': {},
            'by_speaker': {},
        }

    grouped = defaultdict(list)
    for turn in speaker_turns:
        grouped[turn['speaker']].append(turn['text'])

    by_speaker = {}
    by_employee = {}

    for speaker, turns in grouped.items():
        full_text = ' '.join(turns)
        score = sentiment_service.analyze(full_text)
        by_speaker[speaker] = score

    for turn in speaker_turns:
        emp_id = turn.get('employee_id')
        if emp_id is not None:
            by_employee[str(emp_id)] = by_speaker.get(turn['speaker'])

    overall = sentiment_service.analyze(transcript)

    return {
        'overall': overall,
        'by_employee': by_employee,
        'by_speaker': by_speaker,
    }


def analyze_and_store_meeting(employees, transcript: str, date=None, speaker_turns=None):
    if not employees:
        raise ValueError('At least one employee is required for meeting analysis')

    date = date or timezone.now().date()
    speaker_turns = parse_speaker_turns(speaker_turns)
    if not speaker_turns:
        speaker_turns = _build_name_based_turns(transcript, employees)

    owner = employees[0]

    meeting = Meeting.objects.create(
        employee=owner,
        date=date,
        transcript=transcript,
    )

    MeetingParticipant.objects.bulk_create(
        [MeetingParticipant(meeting=meeting, employee=emp) for emp in employees],
        ignore_conflicts=True,
    )

    summary_service = _get_summary_service()
    summary = summary_service.summarize(transcript)

    sentiment_bundle = _sentiment_by_speaker(speaker_turns, transcript)
    participation = _compute_participation(speaker_turns)
    signals = _detect_signals(transcript)

    meeting.summary = summary
    overall_scores = sentiment_bundle.get('overall', {}).get('scores', {})
    meeting.sentiment_score = float(overall_scores.get('positive', 0.0))
    meeting.save(update_fields=['summary', 'sentiment_score', 'updated_at'])

    analysis = MeetingAnalysis.objects.create(
        meeting=meeting,
        transcript=transcript,
        summary=summary,
        employee_sentiment_scores=sentiment_bundle,
        participation_score=participation['score'],
        collaboration_signals=signals['collaboration_signals'],
        engagement_signals=signals['engagement_signals'],
        conflict_detection=signals['conflict_detection'],
        speaker_mapping={'turns': speaker_turns, 'word_counts': participation['per_speaker']},
    )

    _upsert_meeting_insights(meeting, summary, transcript, signals)
    _upsert_employee_insights(meeting, speaker_turns, sentiment_bundle, participation)

    return meeting, analysis


def _upsert_employee_insights(meeting, speaker_turns, sentiment_bundle, participation):
    by_employee_sentiment = sentiment_bundle.get('by_employee', {})
    duration_by_speaker = participation.get('per_speaker_duration', {})
    turns_by_speaker = participation.get('speaking_turns', {})
    interruptions_by_speaker = participation.get('interruption_signals', {})

    mapping = {
        item.speaker_label: item.employee
        for item in meeting.speaker_mappings.select_related('employee').all()
        if item.employee_id
    }

    total_duration = sum(duration_by_speaker.values()) or 0.0
    if total_duration <= 0:
        total_duration = float(participation.get('total_words', 0) or 0)

    buckets = defaultdict(lambda: {
        'duration': 0.0,
        'speaking_turns': 0,
        'interruptions': 0,
    })

    for turn in speaker_turns:
        speaker = turn['speaker']
        employee = mapping.get(speaker)
        if employee is None:
            emp_id = turn.get('employee_id')
            if emp_id:
                employee = meeting.participants.filter(employee_id=emp_id).select_related('employee').first()
                employee = employee.employee if employee else None
        if employee is None:
            continue

        buckets[employee.id]['duration'] += float(duration_by_speaker.get(speaker, 0.0))
        buckets[employee.id]['speaking_turns'] += int(turns_by_speaker.get(speaker, 0))
        buckets[employee.id]['interruptions'] += int(interruptions_by_speaker.get(speaker, 0))

    for participant in meeting.participants.select_related('employee').all():
        employee = participant.employee
        bucket = buckets.get(employee.id, {'duration': 0.0, 'speaking_turns': 0, 'interruptions': 0})
        sentiment_obj = by_employee_sentiment.get(str(employee.id), {})
        sentiment_score = float(sentiment_obj.get('scores', {}).get('positive', 0.0)) if isinstance(sentiment_obj, dict) else 0.0
        engagement_score = (bucket['duration'] / total_duration) if total_duration else 0.0

        EmployeeMeetingInsight.objects.update_or_create(
            employee=employee,
            meeting=meeting,
            defaults={
                'participation_duration': round(bucket['duration'], 3),
                'sentiment_score': round(sentiment_score, 4),
                'engagement_score': round(engagement_score, 4),
                'speaking_turns': int(bucket['speaking_turns']),
                'interruption_signals': int(bucket['interruptions']),
            },
        )


def run_meeting_intelligence_pipeline(meeting_id: int):
    meeting = Meeting.objects.select_related('employee').get(id=meeting_id)
    meeting.transcript_status = Meeting.TRANSCRIPT_STATUS_PROCESSING
    meeting.save(update_fields=['transcript_status', 'updated_at'])

    try:
        with meeting.meeting_file.open('rb') as meeting_file:
            transcription = transcribe_recording(meeting_file)

        full_text = transcription.get('transcript', '').strip()
        segments = transcription.get('segments', [])

        participant_ids = list(meeting.participants.values_list('employee_id', flat=True))
        if not participant_ids and meeting.employee_id:
            participant_ids = [meeting.employee_id]

        diarized = _diarize_segments(segments, speaker_count=max(len(participant_ids), 1))

        participants = list(meeting.participants.select_related('employee'))
        unique_labels = sorted({item['speaker'] for item in diarized})
        label_to_employee_id = {}
        for idx, label in enumerate(unique_labels):
            linked_employee = participants[idx].employee if idx < len(participants) else None
            if linked_employee:
                label_to_employee_id[label] = linked_employee.id
            MeetingSpeakerMapping.objects.update_or_create(
                meeting=meeting,
                speaker_label=label,
                defaults={'employee': linked_employee},
            )

        MeetingTranscript.objects.filter(meeting=meeting).delete()
        transcript_rows = []
        for row in diarized:
            transcript_rows.append(
                MeetingTranscript(
                    meeting=meeting,
                    speaker=row['speaker'],
                    speaker_employee_id=label_to_employee_id.get(row['speaker']),
                    text=row['text'],
                    start_time=row['start'],
                    end_time=row['end'],
                )
            )
        if transcript_rows:
            MeetingTranscript.objects.bulk_create(transcript_rows)

        meeting.transcript = '\n'.join(
            f"[{_to_hh_mm_ss(item['start'])}] {item['speaker']}: {item['text']}" for item in diarized
        )

        if meeting.meeting_date:
            meeting.date = meeting.meeting_date
        if not meeting.meeting_date:
            meeting.meeting_date = meeting.date

        employees = [p.employee for p in participants]
        if not employees and meeting.employee_id:
            employees = [meeting.employee]

        speaker_turns = [
            {
                'speaker': item['speaker'],
                'text': item['text'],
                'start': item['start'],
                'end': item['end'],
            }
            for item in diarized
        ]
        speaker_to_employee = {
            item.speaker_label: item.employee_id
            for item in meeting.speaker_mappings.all()
            if item.employee_id
        }
        for turn in speaker_turns:
            turn['employee_id'] = speaker_to_employee.get(turn['speaker'])

        summary_service = _get_summary_service()
        summary = summary_service.summarize(full_text)

        sentiment_bundle = _sentiment_by_speaker(speaker_turns, full_text)
        participation = _compute_participation(speaker_turns)
        signals = _detect_signals(full_text)

        overall_scores = sentiment_bundle.get('overall', {}).get('scores', {})
        meeting.summary = summary
        meeting.sentiment_score = float(overall_scores.get('positive', 0.0))
        meeting.transcript_status = Meeting.TRANSCRIPT_STATUS_COMPLETED
        meeting.save(update_fields=['transcript', 'summary', 'sentiment_score', 'transcript_status', 'date', 'meeting_date', 'updated_at'])

        MeetingAnalysis.objects.update_or_create(
            meeting=meeting,
            defaults={
                'transcript': meeting.transcript,
                'summary': summary,
                'employee_sentiment_scores': sentiment_bundle,
                'participation_score': participation['score'],
                'collaboration_signals': signals['collaboration_signals'],
                'engagement_signals': signals['engagement_signals'],
                'conflict_detection': signals['conflict_detection'],
                'speaker_mapping': {
                    'turns': speaker_turns,
                    'word_counts': participation['per_speaker'],
                    'durations': participation['per_speaker_duration'],
                    'speaking_turns': participation['speaking_turns'],
                    'interruption_signals': participation['interruption_signals'],
                },
            },
        )

        _upsert_meeting_insights(meeting, summary, meeting.transcript, signals)
        _upsert_employee_insights(meeting, speaker_turns, sentiment_bundle, participation)
        return meeting
    except Exception as exc:
        logger.exception('Meeting intelligence failed for meeting_id=%s: %s', meeting_id, exc)
        meeting.transcript_status = Meeting.TRANSCRIPT_STATUS_FAILED
        meeting.save(update_fields=['transcript_status', 'updated_at'])
        return meeting
