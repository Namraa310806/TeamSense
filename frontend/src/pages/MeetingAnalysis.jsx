import { useEffect, useMemo, useState } from 'react';
import {
  Upload,
  Sparkles,
  Users,
  Activity,
  MessageSquare,
  FileAudio,
} from 'lucide-react';
import {
  fetchEmployees,
  fetchMeetings,
  fetchMeeting,
  fetchMeetingInsights,
  uploadMeeting,
} from '../services/api';

function sentimentColor(score = 0) {
  if (score >= 0.65) return 'text-green-600';
  if (score >= 0.45) return 'text-amber-600';
  return 'text-rose-600';
}

function statusClass(status) {
  const value = String(status || '').toUpperCase();
  if (value === 'COMPLETED') return 'bg-green-50 text-green-700 border-green-200';
  if (value === 'PROCESSING') return 'bg-cyan-50 text-cyan-700 border-cyan-200';
  if (value === 'FAILED') return 'bg-rose-50 text-rose-700 border-rose-200';
  return 'bg-amber-50 text-amber-700 border-amber-200';
}

function normalizeName(employee) {
  if (!employee) return 'Unnamed Employee';
  return employee.name || employee.employee_name || employee.full_name || employee.username || `Employee #${employee.id}`;
}

function formatTimestampSeconds(value) {
  const total = Math.max(0, Math.floor(Number(value || 0)));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const seconds = total % 60;
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

function fallbackTranscriptLines(rawTranscript) {
  if (!rawTranscript) return [];
  return rawTranscript
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      const match = line.match(/^\[(.*?)\]\s*([^:]+):\s*(.*)$/);
      if (!match) {
        return {
          id: `line-${index}`,
          speaker: 'Speaker',
          speaker_employee_name: 'Speaker',
          text: line,
          start_time: 0,
        };
      }
      return {
        id: `line-${index}`,
        speaker: match[2],
        speaker_employee_name: match[2],
        text: match[3],
        start_time: 0,
      };
    });
}

function MeetingAnalysis() {
  const [employees, setEmployees] = useState([]);
  const [employeeLoadError, setEmployeeLoadError] = useState('');

  const [selectedEmployeeIds, setSelectedEmployeeIds] = useState([]);
  const [meetingFile, setMeetingFile] = useState(null);
  const [transcriptText, setTranscriptText] = useState('');
  const [meetingTitle, setMeetingTitle] = useState('Weekly Team Sync');
  const [department, setDepartment] = useState('Engineering');
  const [meetingDate, setMeetingDate] = useState('');
  const [organizationId, setOrganizationId] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const [meetings, setMeetings] = useState([]);
  const [selectedMeetingId, setSelectedMeetingId] = useState(null);
  const [selectedMeeting, setSelectedMeeting] = useState(null);
  const [selectedMeetingInsights, setSelectedMeetingInsights] = useState(null);
  const [loadingMeetingDetails, setLoadingMeetingDetails] = useState(false);

  const selectedMeetingTranscriptSegments = useMemo(() => {
    if (Array.isArray(selectedMeeting?.transcript_segments) && selectedMeeting.transcript_segments.length > 0) {
      return selectedMeeting.transcript_segments;
    }
    return fallbackTranscriptLines(selectedMeeting?.transcript || '');
  }, [selectedMeeting]);

  const selectedMeetingParticipants = useMemo(() => {
    if (!selectedMeeting) return '';
    const names = selectedMeeting.participant_names || [];
    if (names.length > 0) return names.join(', ');
    return selectedMeeting.employee_name || 'Unknown participants';
  }, [selectedMeeting]);

  const shouldScrollMeetingList = meetings.length > 8;
  const insightItems = selectedMeetingInsights?.meeting_insights || [];
  const shouldScrollInsightItems = insightItems.length > 8;
  const shouldScrollTranscript = selectedMeetingTranscriptSegments.length > 14;

  const loadEmployees = async () => {
    try {
      const res = await fetchEmployees();
      const data = Array.isArray(res.data?.results) ? res.data.results : res.data;
      setEmployees(Array.isArray(data) ? data : []);
      setEmployeeLoadError('');
    } catch (err) {
      setEmployees([]);
      const apiMessage = err?.response?.data?.detail || err?.response?.data?.error;
      setEmployeeLoadError(apiMessage || 'Unable to load employees. Please login again and refresh.');
    }
  };

  const loadMeetings = async (focusMeetingId = null) => {
    try {
      const res = await fetchMeetings();
      const list = Array.isArray(res.data?.results) ? res.data.results : res.data;
      const safeList = Array.isArray(list) ? list : [];
      setMeetings(safeList);

      if (focusMeetingId) {
        setSelectedMeetingId(focusMeetingId);
      } else if (!selectedMeetingId && safeList.length > 0) {
        setSelectedMeetingId(safeList[0].id);
      }
    } catch {
      setMeetings([]);
    }
  };

  const loadMeetingDetails = async (meetingId) => {
    if (!meetingId) return;
    setLoadingMeetingDetails(true);
    try {
      const [meetingRes, insightsRes] = await Promise.all([
        fetchMeeting(meetingId),
        fetchMeetingInsights(meetingId).catch(() => ({ data: null })),
      ]);

      setSelectedMeeting(meetingRes.data);
      setSelectedMeetingInsights(insightsRes.data);
    } catch {
      setSelectedMeeting(null);
      setSelectedMeetingInsights(null);
    } finally {
      setLoadingMeetingDetails(false);
    }
  };

  useEffect(() => {
    loadEmployees();
    loadMeetings();
  }, []);

  useEffect(() => {
    if (selectedMeetingId) {
      loadMeetingDetails(selectedMeetingId);
    }
  }, [selectedMeetingId]);

  useEffect(() => {
    if (!selectedMeeting || (selectedMeeting.transcript_status !== 'PENDING' && selectedMeeting.transcript_status !== 'PROCESSING')) {
      return;
    }

    const timer = setInterval(async () => {
      try {
        const res = await fetchMeeting(selectedMeeting.id);
        setSelectedMeeting(res.data);
        if (res.data.transcript_status === 'COMPLETED' || res.data.transcript_status === 'FAILED') {
          const insightsRes = await fetchMeetingInsights(res.data.id).catch(() => ({ data: null }));
          setSelectedMeetingInsights(insightsRes.data);
          loadMeetings(res.data.id);
        }
      } catch {
        // ignore transient polling errors
      }
    }, 5000);

    return () => clearInterval(timer);
  }, [selectedMeeting]);

  const onSubmit = async (event) => {
    event.preventDefault();
    setError('');

    if (selectedEmployeeIds.length === 0) {
      setError('Please select at least one employee participant.');
      return;
    }
    if (!meetingFile && !transcriptText.trim()) {
      setError('Please provide transcript text or upload a recording (mp3, wav, mp4).');
      return;
    }

    const formData = new FormData();
    formData.append('participants', JSON.stringify(selectedEmployeeIds));
    if (meetingFile) {
      formData.append('meeting_file', meetingFile);
    }
    if (transcriptText.trim()) {
      formData.append('transcript_text', transcriptText.trim());
    }
    formData.append('meeting_title', meetingTitle);
    formData.append('department', department);
    if (meetingDate) formData.append('meeting_date', meetingDate);
    if (organizationId) formData.append('organization_id', organizationId);

    setSubmitting(true);
    try {
      const response = await uploadMeeting(formData);
      const createdId = response?.data?.meeting?.id;
      setMeetingFile(null);
      setTranscriptText('');
      await loadMeetings(createdId);
      if (createdId) await loadMeetingDetails(createdId);
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to upload and analyze meeting.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="glass-card p-6 bg-gradient-to-r from-green-50 via-emerald-50 to-cyan-50 border border-green-200">
        <h1 className="text-2xl font-bold text-slate-800">Meeting Intelligence</h1>
        <p className="text-slate-600 mt-2 text-sm">
          Upload recordings, run open-source Whisper speech-to-text, map speakers to employees, and store actionable employee-level insights.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <form onSubmit={onSubmit} className="glass-card p-6 space-y-4 xl:col-span-1">
          <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <Upload className="w-5 h-5 text-green-600" /> Upload Meeting
          </h2>

          <div>
            <label className="block text-sm font-medium text-slate-600 mb-2">Meeting Title</label>
            <input
              type="text"
              value={meetingTitle}
              onChange={(e) => setMeetingTitle(e.target.value)}
              className="w-full bg-white border border-gray-200 rounded-xl px-3 py-2 text-slate-800 placeholder-gray-400 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/20"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-slate-600 mb-2">Department</label>
              <input
                type="text"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-xl px-3 py-2 text-slate-800 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/20"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-600 mb-2">Meeting Date</label>
              <input
                type="date"
                value={meetingDate}
                onChange={(e) => setMeetingDate(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-xl px-3 py-2 text-slate-800 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/20"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-600 mb-2">Organization ID (optional)</label>
            <input
              type="number"
              value={organizationId}
              onChange={(e) => setOrganizationId(e.target.value)}
              className="w-full bg-white border border-gray-200 rounded-xl px-3 py-2 text-slate-800 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/20"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-600 mb-2">Participants</label>
            <select
              multiple
              value={selectedEmployeeIds.map(String)}
              onChange={(e) => {
                const values = Array.from(e.target.selectedOptions).map((opt) => Number(opt.value));
                setSelectedEmployeeIds(values);
              }}
              className="w-full min-h-28 bg-white border border-gray-200 rounded-xl px-3 py-2 text-slate-800 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/20"
            >
              {employees.map((emp) => (
                <option key={emp.id} value={emp.id}>{normalizeName(emp)}</option>
              ))}
            </select>
            <p className="text-xs text-slate-500 mt-1">Ctrl/Cmd + click to select multiple employees.</p>
            {employeeLoadError && <p className="text-xs text-rose-600 mt-2">{employeeLoadError}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-600 mb-2">Recording File</label>
            <label className="flex items-center gap-3 bg-white border border-dashed border-gray-300 rounded-xl px-3 py-3 text-slate-600 cursor-pointer hover:border-green-400 transition-colors">
              <FileAudio className="w-5 h-5 text-cyan-600" />
              <span className="text-sm truncate">{meetingFile?.name || 'Choose mp3 / wav / mp4 file'}</span>
              <input
                type="file"
                accept=".mp3,.wav,.mp4,audio/*,video/mp4"
                onChange={(e) => setMeetingFile(e.target.files?.[0] || null)}
                className="hidden"
              />
            </label>
            <p className="text-xs text-slate-500 mt-1">Optional when transcript is provided.</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-600 mb-2">Transcript Text (optional)</label>
            <textarea
              value={transcriptText}
              onChange={(e) => setTranscriptText(e.target.value)}
              rows={5}
              placeholder="Paste transcript text here. If added, this will be used directly and speech-to-text is skipped."
              className="w-full bg-white border border-gray-200 rounded-xl px-3 py-2 text-slate-800 placeholder-gray-400 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/20"
            />
            <p className="text-xs text-slate-500 mt-1">Transcript has priority when both transcript and recording are provided.</p>
          </div>

          {error && <p className="text-sm text-rose-600">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-green-600 to-emerald-500 hover:from-green-500 hover:to-emerald-400 text-white font-semibold disabled:opacity-60"
          >
            {submitting ? 'AI is analyzing the meeting...' : 'Upload & Analyze Meeting'}
          </button>
        </form>

        <div className="xl:col-span-2 grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
          <div className="glass-card p-6 min-h-[520px] flex flex-col">
            <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2 mb-4">
              <Users className="w-5 h-5 text-cyan-600" /> Meeting List
            </h2>

            <div className={`space-y-3 pr-1 flex-1 ${shouldScrollMeetingList ? 'max-h-[640px] overflow-y-auto' : ''}`}>
              {meetings.map((meeting) => (
                <button
                  key={meeting.id}
                  onClick={() => setSelectedMeetingId(meeting.id)}
                  className={`w-full text-left rounded-xl border px-4 py-3 transition-colors ${
                    selectedMeetingId === meeting.id
                      ? 'bg-green-50 border-green-200'
                      : 'bg-white border-gray-200 hover:border-cyan-300 hover:bg-cyan-50/30'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-slate-800 font-medium">{meeting.meeting_title || `Meeting #${meeting.id}`}</p>
                      <p className="text-xs text-slate-500 mt-1">{meeting.meeting_date || meeting.date} • {meeting.department || 'Department N/A'}</p>
                    </div>
                    <span className={`text-sm font-semibold ${sentimentColor(meeting.sentiment_score || 0)}`}>
                      {meeting.sentiment_score != null ? (meeting.sentiment_score).toFixed(2) : 'N/A'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-2 break-words">Participants: {(meeting.participant_names || []).join(', ') || meeting.employee_name || 'N/A'}</p>
                  <div className="mt-2">
                    <span className={`inline-flex px-2 py-0.5 rounded-md border text-xs ${statusClass(meeting.transcript_status)}`}>
                      {meeting.transcript_status || 'PENDING'}
                    </span>
                  </div>
                </button>
              ))}

              {meetings.length === 0 && (
                <p className="text-slate-500 text-sm">No meetings found yet. Upload a recording to start analysis.</p>
              )}
            </div>
          </div>

          <div className="glass-card p-6 min-h-[520px] flex flex-col">
            <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-emerald-600" /> AI Insights Panel
            </h2>

            {!selectedMeeting && !loadingMeetingDetails && <p className="text-slate-500 text-sm">Select a meeting to view transcript and insights.</p>}
            {loadingMeetingDetails && <p className="text-slate-500 text-sm">Loading meeting details...</p>}

            {selectedMeeting && (
              <div className="space-y-4 text-sm flex-1">
                <div>
                  <p className="text-xs text-slate-500">Meeting</p>
                  <p className="text-slate-800 font-medium">{selectedMeeting.meeting_title || `Meeting #${selectedMeeting.id}`}</p>
                  <p className="text-xs text-slate-500 mt-1">{selectedMeetingParticipants}</p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-white border border-gray-200 rounded-lg p-3">
                    <p className="text-xs text-slate-500">Team Sentiment</p>
                    <p className={`font-semibold mt-1 ${sentimentColor(selectedMeetingInsights?.team_sentiment_score || selectedMeeting.sentiment_score || 0)}`}>
                      {((selectedMeetingInsights?.team_sentiment_score ?? selectedMeeting.sentiment_score ?? 0) * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-lg p-3">
                    <p className="text-xs text-slate-500">Status</p>
                    <span className={`inline-flex px-2 py-0.5 rounded-md border text-xs mt-1 ${statusClass(selectedMeeting.transcript_status)}`}>
                      {selectedMeeting.transcript_status}
                    </span>
                  </div>
                </div>

                {(selectedMeeting.transcript_status === 'PENDING' || selectedMeeting.transcript_status === 'PROCESSING') && (
                  <div className="bg-cyan-50 border border-cyan-200 rounded-lg p-3 text-cyan-700 text-xs">
                    AI is analyzing the meeting. Whisper speech-to-text and participant mapping are in progress.
                  </div>
                )}

                <div>
                  <p className="text-xs text-slate-500 mb-2">Meeting Summary</p>
                  <div className="bg-white border border-gray-200 rounded-lg p-3 text-slate-700 text-xs leading-relaxed">
                    {selectedMeetingInsights?.analysis?.summary || selectedMeeting.summary || 'Summary will appear after analysis completes.'}
                  </div>
                </div>

                <div>
                  <p className="text-xs text-slate-500 mb-2">Action Items / Topics / Risks</p>
                  <div className={`space-y-2 pr-1 ${shouldScrollInsightItems ? 'max-h-64 overflow-y-auto' : ''}`}>
                    {insightItems.map((insight) => (
                      <div key={insight.id} className="bg-white border border-gray-200 rounded-lg p-2 text-xs text-slate-700">
                        <span className="text-cyan-600 font-medium mr-1">{insight.insight_type}:</span>
                        {insight.description}
                      </div>
                    ))}
                    {insightItems.length === 0 && (
                      <p className="text-slate-500 text-xs">Insights will appear after analysis.</p>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-white border border-gray-200 rounded-lg p-3">
                    <p className="text-xs text-slate-500">Top Contributors</p>
                    <p className="text-slate-800 font-semibold mt-1">{selectedMeetingInsights?.top_contributors?.length || 0}</p>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-lg p-3">
                    <p className="text-xs text-slate-500">Low Participation</p>
                    <p className="text-slate-800 font-semibold mt-1">{selectedMeetingInsights?.low_participation_employees?.length || 0}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2 mb-4">
          <MessageSquare className="w-5 h-5 text-cyan-600" /> Transcript Viewer
        </h2>

        {!selectedMeeting && <p className="text-slate-500 text-sm">Choose a meeting to view transcript chat.</p>}

        {selectedMeeting && (
          <div className={`space-y-3 pr-1 ${shouldScrollTranscript ? 'max-h-[520px] overflow-y-auto' : ''}`}>
            {selectedMeetingTranscriptSegments.map((segment) => (
              <div key={segment.id} className="bg-white border border-gray-200 rounded-xl px-4 py-3">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-cyan-700 text-sm font-medium">
                    {segment.speaker_employee_name || segment.speaker || 'Speaker'}
                  </p>
                  <p className="text-slate-500 text-xs">{formatTimestampSeconds(segment.start_time)}</p>
                </div>
                <p className="text-slate-700 text-sm leading-relaxed">{segment.text}</p>
              </div>
            ))}

            {selectedMeetingTranscriptSegments.length === 0 && (
              <p className="text-slate-500 text-sm">Transcript not available yet.</p>
            )}
          </div>
        )}
      </div>

      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2 mb-4">
          <Activity className="w-5 h-5 text-green-600" /> Employee Profile Integration
        </h2>
        <p className="text-slate-600 text-sm">
          Meeting-level and employee-level insights from each analyzed meeting are saved and available in employee profile intelligence sections.
        </p>
      </div>
    </div>
  );
}

export default MeetingAnalysis;
