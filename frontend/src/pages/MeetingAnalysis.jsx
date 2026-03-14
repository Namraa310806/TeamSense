import { useEffect, useMemo, useState } from 'react';
import { Upload, Activity, Users, MessageSquareWarning, Sparkles } from 'lucide-react';
import {
  fetchEmployees,
  fetchEmployeeMeetingInsights,
  uploadMeeting,
} from '../services/api';

function MeetingAnalysis() {
  const [employees, setEmployees] = useState([]);
  const [selectedEmployeeIds, setSelectedEmployeeIds] = useState([]);
  const [meetingFile, setMeetingFile] = useState(null);
  const [meetingTitle, setMeetingTitle] = useState('Weekly Team Sync');
  const [department, setDepartment] = useState('Engineering');
  const [meetingDate, setMeetingDate] = useState('');
  const [organizationId, setOrganizationId] = useState('');
  const [speakerTurns, setSpeakerTurns] = useState('[]');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [employeeLoadError, setEmployeeLoadError] = useState('');
  const [result, setResult] = useState(null);
  const [insights, setInsights] = useState(null);

  const getEmployeeName = (employee) => {
    if (!employee) return 'Unnamed Employee';
    return employee.name || employee.employee_name || employee.full_name || employee.username || `Employee #${employee.id}`;
  };

  useEffect(() => {
    fetchEmployees()
      .then((res) => {
        const data = Array.isArray(res.data?.results) ? res.data.results : res.data;
        setEmployees(Array.isArray(data) ? data : []);
        setEmployeeLoadError('');
      })
      .catch((err) => {
        setEmployees([]);
        const apiMessage = err?.response?.data?.detail || err?.response?.data?.error;
        setEmployeeLoadError(apiMessage || 'Unable to load employees. Please login again and refresh.');
      });
  }, []);

  useEffect(() => {
    const focusEmployeeId = selectedEmployeeIds[0];
    if (!focusEmployeeId) {
      setInsights(null);
      return;
    }

    fetchEmployeeMeetingInsights(focusEmployeeId)
      .then((res) => setInsights(res.data))
      .catch(() => setInsights(null));
  }, [selectedEmployeeIds, result]);

  const selectedName = useMemo(() => {
    const found = employees.find((e) => String(e.id) === String(selectedEmployeeIds[0] || ''));
    return found ? getEmployeeName(found) : 'Employee';
  }, [employees, selectedEmployeeIds]);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setResult(null);

    if (selectedEmployeeIds.length === 0) {
      setError('Please select at least one employee.');
      return;
    }
    if (!meetingFile) {
      setError('Please upload a recording file.');
      return;
    }

    const formData = new FormData();
    formData.append('participants', JSON.stringify(selectedEmployeeIds));
    formData.append('meeting_file', meetingFile);
    formData.append('meeting_title', meetingTitle);
    formData.append('department', department);
    if (meetingDate) {
      formData.append('meeting_date', meetingDate);
    }
    if (organizationId) {
      formData.append('organization_id', organizationId);
    }

    const trimmed = speakerTurns.trim();
    if (trimmed && trimmed !== '[]') {
      formData.append('speaker_turns', trimmed);
    }

    setLoading(true);
    try {
      const res = await uploadMeeting(formData);
      setResult(res.data);
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to process recording.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="glass-card p-6">
        <h1 className="text-2xl font-bold text-white">Meeting Intelligence</h1>
        <p className="text-slate-400 mt-2 text-sm">
          Upload mp3/wav/mp4 recordings to generate transcript, sentiment, engagement, conflict, and participation insights for one or more employees.
        </p>
        <p className="text-slate-500 mt-2 text-xs">
          If speaker tags are not provided, the system automatically maps transcript segments to selected employee names using heuristic name matching.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <form onSubmit={onSubmit} className="glass-card p-6 space-y-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Upload className="w-5 h-5 text-primary-400" /> Upload Recording
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-sm text-slate-300 mb-2">Meeting Title</label>
              <input
                type="text"
                value={meetingTitle}
                onChange={(e) => setMeetingTitle(e.target.value)}
                className="w-full bg-surface-800 border border-surface-700 rounded-xl px-3 py-2 text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-300 mb-2">Department</label>
              <input
                type="text"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full bg-surface-800 border border-surface-700 rounded-xl px-3 py-2 text-white"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-sm text-slate-300 mb-2">Meeting Date</label>
              <input
                type="date"
                value={meetingDate}
                onChange={(e) => setMeetingDate(e.target.value)}
                className="w-full bg-surface-800 border border-surface-700 rounded-xl px-3 py-2 text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-300 mb-2">Organization ID (optional)</label>
              <input
                type="number"
                value={organizationId}
                onChange={(e) => setOrganizationId(e.target.value)}
                className="w-full bg-surface-800 border border-surface-700 rounded-xl px-3 py-2 text-white"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-slate-300 mb-2">Employees in this meeting</label>
            <select
              multiple
              className="w-full bg-surface-800 border border-surface-700 rounded-xl px-3 py-2 text-white min-h-28"
              value={selectedEmployeeIds.map(String)}
              onChange={(e) => {
                const values = Array.from(e.target.selectedOptions).map((opt) => Number(opt.value));
                setSelectedEmployeeIds(values);
              }}
            >
              {employees.map((emp) => (
                <option key={emp.id} value={emp.id}>{getEmployeeName(emp)}</option>
              ))}
            </select>
            <p className="text-xs text-slate-500 mt-2">Hold Ctrl/Cmd to select multiple employees.</p>
            {employeeLoadError && <p className="text-xs text-accent-rose mt-2">{employeeLoadError}</p>}
            {!employeeLoadError && employees.length === 0 && (
              <p className="text-xs text-accent-amber mt-2">No employees available for your account/organization.</p>
            )}
          </div>

          <div>
            <label className="block text-sm text-slate-300 mb-2">Recording (mp3, wav, mp4)</label>
            <input
              type="file"
              accept=".mp3,.wav,.mp4,audio/*,video/mp4"
              onChange={(e) => setMeetingFile(e.target.files?.[0] || null)}
              className="w-full bg-surface-800 border border-surface-700 rounded-xl px-3 py-2 text-slate-200"
            />
          </div>

          <div>
            <label className="block text-sm text-slate-300 mb-2">Speaker Turns (optional JSON)</label>
            <textarea
              rows={5}
              value={speakerTurns}
              onChange={(e) => setSpeakerTurns(e.target.value)}
              className="w-full bg-surface-800 border border-surface-700 rounded-xl px-3 py-2 text-slate-200 font-mono text-xs"
              placeholder='[{"speaker":"SPEAKER_1","employee_id":1,"text":"..."}]'
            />
          </div>

          {error && <p className="text-accent-rose text-sm">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary-600 hover:bg-primary-500 disabled:opacity-60 text-white rounded-xl py-2.5 font-medium"
          >
            {loading ? 'Processing...' : 'Analyze Meeting'}
          </button>
        </form>

        <div className="glass-card p-6 space-y-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-accent-cyan" /> Latest Output
          </h2>

          {!result && <p className="text-slate-500 text-sm">Upload a recording to view analysis output.</p>}

          {result?.meeting && (
            <div className="space-y-3 text-sm">
              <div>
                <p className="text-slate-400">Meeting ID</p>
                <p className="text-white font-medium">{result.meeting.id}</p>
              </div>
              <div>
                <p className="text-slate-400">Processing Status</p>
                <p className="text-slate-200 capitalize">{result.pipeline_status || result.meeting.transcript_status?.toLowerCase() || 'queued'}</p>
              </div>
              {Array.isArray(result.participants) && result.participants.length > 0 && (
                <div>
                  <p className="text-slate-400 mb-1">Participants</p>
                  <p className="text-slate-200">{result.participants.map((p) => p?.name || `Employee #${p?.id}`).join(', ')}</p>
                </div>
              )}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-surface-900/60 border border-surface-700 rounded-lg p-3">
                  <p className="text-slate-500 text-xs">Participation</p>
                  <p className="text-primary-300 font-semibold">{Math.round((result.analysis?.participation_score || 0) * 100)}%</p>
                </div>
                <div className="bg-surface-900/60 border border-surface-700 rounded-lg p-3">
                  <p className="text-slate-500 text-xs">Engagement</p>
                  <p className="text-accent-emerald font-semibold">{result.analysis?.engagement_signals?.level || '-'}</p>
                </div>
                <div className="bg-surface-900/60 border border-surface-700 rounded-lg p-3">
                  <p className="text-slate-500 text-xs">Conflict</p>
                  <p className="text-accent-amber font-semibold">{result.analysis?.conflict_detection?.level || '-'}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Employee Meeting Insights</h2>
        {selectedEmployeeIds.length === 0 && <p className="text-slate-500 text-sm">Select at least one employee to see trends.</p>}
        {selectedEmployeeIds.length > 0 && !insights && <p className="text-slate-500 text-sm">No analysis data found for {selectedName}.</p>}

        {insights && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-surface-900/60 border border-surface-700 rounded-xl p-4">
              <p className="text-slate-400 text-xs flex items-center gap-2"><Activity className="w-4 h-4" /> Engagement Score</p>
              <p className="text-2xl font-bold text-primary-300 mt-1">{Math.round((insights.engagement_score || 0) * 100)}%</p>
            </div>
            <div className="bg-surface-900/60 border border-surface-700 rounded-xl p-4">
              <p className="text-slate-400 text-xs flex items-center gap-2"><Users className="w-4 h-4" /> Participation Frequency</p>
              <p className="text-2xl font-bold text-accent-cyan mt-1">{insights.meeting_count || 0}</p>
            </div>
            <div className="bg-surface-900/60 border border-surface-700 rounded-xl p-4">
              <p className="text-slate-400 text-xs flex items-center gap-2"><MessageSquareWarning className="w-4 h-4" /> Latest Conflict Level</p>
              <p className="text-2xl font-bold text-accent-amber mt-1">{insights.latest_analysis?.conflict_detection?.level || 'low'}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default MeetingAnalysis;
