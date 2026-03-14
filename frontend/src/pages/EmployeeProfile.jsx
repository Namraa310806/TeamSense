import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, User, Briefcase, Calendar, Mail, TrendingUp, AlertTriangle, MessageSquare, Brain, Target, AlertCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { fetchEmployee, fetchAttrition, fetchEmployeeMeetingInsights, uploadMeeting } from '../services/api';

function EmployeeProfile() {
  const { id } = useParams();
  const [employee, setEmployee] = useState(null);
  const [attrition, setAttrition] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [uploading, setUploading] = useState(false);
  const [meetingIntelligence, setMeetingIntelligence] = useState(null);

  useEffect(() => {
    Promise.all([
      fetchEmployee(id).then((r) => r.data).catch(() => null),
      fetchAttrition(id).then((r) => r.data).catch(() => null),
      fetchEmployeeMeetingInsights(id).then((r) => r.data).catch(() => null),
    ]).then(([empData, attrData, meetingIntel]) => {
      setEmployee(empData || {
        id, name: 'Employee', role: 'Role', department: 'Department',
        join_date: '2024-01-15', manager: 'Manager', email: 'employee@teamsense.ai',
        meetings: [], insights: null, meeting_count: 0, avg_sentiment: 0.65,
      });
      setAttrition(attrData || { risk_score: 0.3, risk_level: 'low', factors: ['No data'] });
      setMeetingIntelligence(meetingIntel);
      setLoading(false);
    });
  }, [id]);

  const handleUpload = async () => {
    if (!transcript.trim()) return;
    setUploading(true);
    try {
      await uploadMeeting({ employee_id: parseInt(id), transcript });
      setTranscript('');
      setShowUpload(false);
      // Reload both data
      const [empRes, attrRes] = await Promise.all([
        fetchEmployee(id),
        fetchAttrition(id)
      ]);
      setEmployee(empRes.data);
      setAttrition(attrRes.data);
    } catch (err) {
      console.error('Upload failed:', err);
    }
    setUploading(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="w-16 h-16 rounded-full border-4 border-green-200 border-t-green-500 animate-spin"></div>
      </div>
    );
  }

  const meetings = employee?.meetings || [];
  const insights = employee?.insights;
  const sentimentData = meetings.map((m, i) => ({
    date: m.date,
    sentiment: m.sentiment_score,
    index: i + 1,
  })).reverse();

  const riskColor = {
    critical: 'text-red-600 bg-red-50 border-red-200',
    high: 'text-rose-600 bg-rose-50 border-rose-200',
    medium: 'text-amber-600 bg-amber-50 border-amber-200',
    low: 'text-green-600 bg-green-50 border-green-200',
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Back & Header */}
      <div className="animate-slide-up">
        <Link to="/employees" className="flex items-center gap-2 text-slate-500 hover:text-slate-800 text-sm mb-4 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Employees
        </Link>
        <div className="glass-card p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-5">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-green-500 to-green-400 flex items-center justify-center shadow-lg shadow-green-500/20">
                <span className="text-2xl font-bold text-white">{employee?.name?.charAt(0)}</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-800">{employee?.name}</h1>
                <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
                  <span className="flex items-center gap-1"><Briefcase className="w-4 h-4" />{employee?.role}</span>
                  <span className="flex items-center gap-1"><User className="w-4 h-4" />{employee?.department}</span>
                  <span className="flex items-center gap-1"><Calendar className="w-4 h-4" />Joined {employee?.join_date}</span>
                </div>
                {employee?.email && (
                  <p className="flex items-center gap-1 text-xs text-slate-400 mt-1">
                    <Mail className="w-3 h-3" />{employee.email}
                  </p>
                )}
              </div>
            </div>
            <button
              onClick={() => setShowUpload(!showUpload)}
              className="px-4 py-2 bg-gradient-to-r from-green-600 to-green-500 text-white rounded-xl text-sm font-medium hover:shadow-lg hover:shadow-green-500/20 transition-all"
            >
              Upload Meeting
            </button>
          </div>
        </div>
      </div>

      {/* Upload form */}
      {showUpload && (
        <div className="glass-card p-6 animate-slide-up">
          <h3 className="text-slate-800 font-semibold mb-3">Upload Meeting Transcript</h3>
          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="Paste the meeting transcript here..."
            className="w-full h-40 bg-white border border-gray-200 rounded-xl p-4 text-slate-800 text-sm resize-none focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/20 transition-colors placeholder-gray-400"
          />
          <div className="flex gap-3 mt-3">
            <button
              onClick={handleUpload}
              disabled={uploading || !transcript.trim()}
              className="px-6 py-2.5 bg-green-600 hover:bg-green-500 text-white rounded-xl text-sm font-medium disabled:opacity-50 transition-colors shadow-sm shadow-green-500/20"
            >
              {uploading ? 'Processing...' : 'Upload & Analyze'}
            </button>
            <button onClick={() => setShowUpload(false)} className="px-6 py-2.5 bg-gray-100 hover:bg-gray-200 text-slate-600 rounded-xl text-sm transition-colors">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Sentiment Chart */}
        <div className="glass-card p-6 md:col-span-2 animate-fade-in">
          <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-500" />
            Sentiment Trend
          </h2>
          {sentimentData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={sentimentData}>
                <defs>
                  <linearGradient id="sentimentGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 1]} tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: 'rgba(255,255,255,0.97)', border: '1px solid #e5e7eb', borderRadius: '12px', fontSize: '12px' }}
                  labelStyle={{ color: '#1e293b' }}
                />
                <Area type="monotone" dataKey="sentiment" stroke="#22c55e" fill="url(#sentimentGradient)" strokeWidth={2} dot={{ fill: '#22c55e', r: 4 }} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-slate-400 text-center py-10">No sentiment data yet</p>
          )}
        </div>

        {/* Attrition Risk */}
        <div className="glass-card p-6 animate-fade-in">
          <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            Attrition Risk
          </h2>
          {attrition && (
            <div className="text-center">
              <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full border font-semibold text-sm ${riskColor[attrition.risk_level] || riskColor.low}`}>
                {attrition.risk_level?.toUpperCase()}
              </div>
              <div className="mt-4">
                <div className="text-4xl font-bold text-slate-800">{(attrition.risk_score * 100).toFixed(0)}%</div>
                <p className="text-xs text-slate-400 mt-1">Risk Score</p>
              </div>
              <div className="mt-4 space-y-2">
                {attrition.factors?.map((f, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-slate-500">
                    <AlertCircle className="w-3 h-3 mt-0.5 text-amber-500 flex-shrink-0" />
                    {f}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* AI Insights */}
      {insights && (
        <div className="glass-card p-6 animate-fade-in">
          <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <Brain className="w-5 h-5 text-violet-500" />
            AI Insights
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h3 className="text-sm font-medium text-slate-500 mb-2 flex items-center gap-1">
                <Target className="w-4 h-4" /> Topics
              </h3>
              <div className="flex flex-wrap gap-2">
                {(insights.topics || []).map((t, i) => (
                  <span key={i} className="text-xs px-3 py-1.5 rounded-full bg-green-50 text-green-700 border border-green-200">
                    {t.topic || t}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-sm font-medium text-slate-500 mb-2">Career Goals</h3>
              <p className="text-sm text-slate-800">{insights.career_goals || 'Not identified yet'}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-slate-500 mb-2">Concerns</h3>
              <p className="text-sm text-slate-800">{insights.concerns || 'No concerns flagged'}</p>
            </div>
          </div>
        </div>
      )}

      {/* AI Meeting Insights */}
      <div className="glass-card p-6 animate-fade-in">
        <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
          <Brain className="w-5 h-5 text-cyan-500" />
          AI Meeting Insights
        </h2>

        {!meetingIntelligence && (
          <p className="text-slate-500 text-sm">No employee-level meeting intelligence available yet.</p>
        )}

        {meetingIntelligence && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="bg-white border border-gray-200 rounded-xl p-3">
                <p className="text-xs text-slate-500">Meetings Analyzed</p>
                <p className="text-lg font-semibold text-slate-800 mt-1">{meetingIntelligence.meeting_count || 0}</p>
              </div>
              <div className="bg-white border border-gray-200 rounded-xl p-3">
                <p className="text-xs text-slate-500">Engagement</p>
                <p className="text-lg font-semibold text-green-600 mt-1">{Math.round((meetingIntelligence.engagement_score || 0) * 100)}%</p>
              </div>
              <div className="bg-white border border-gray-200 rounded-xl p-3">
                <p className="text-xs text-slate-500">Latest Sentiment</p>
                <p className="text-lg font-semibold text-slate-800 mt-1">{meetingIntelligence.latest_analysis?.employee_sentiment_scores?.overall?.label || 'N/A'}</p>
              </div>
            </div>

            <div className="space-y-2">
              {(meetingIntelligence.insights || []).slice(0, 6).map((entry) => (
                <div key={entry.id} className="bg-gray-50 border border-gray-200 rounded-xl p-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-800">Meeting #{entry.meeting}</p>
                    <p className="text-xs text-slate-500 mt-1">
                      Sentiment: {entry.sentiment_score?.toFixed?.(2) || entry.sentiment_score} • Turns: {entry.speaking_turns}
                    </p>
                  </div>
                  <p className="text-sm font-semibold text-cyan-600">Engagement {(Number(entry.engagement_score || 0) * 100).toFixed(0)}%</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Meeting Timeline */}
      <div className="glass-card p-6 animate-fade-in">
        <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-cyan-500" />
          Meeting Timeline
        </h2>
        {meetings.length > 0 ? (
          <div className="space-y-3">
            {meetings.map((meeting) => (
              <Link
                key={meeting.id}
                to={`/meetings/${meeting.id}`}
                className="flex items-center justify-between p-4 rounded-xl bg-gray-50 hover:bg-green-50 border border-gray-100 hover:border-green-200 transition-all group"
              >
                <div className="flex items-center gap-4">
                  <div className="w-2 h-2 rounded-full" style={{
                    backgroundColor: meeting.sentiment_score > 0.6 ? '#10b981' : meeting.sentiment_score > 0.4 ? '#f59e0b' : '#f43f5e'
                  }} />
                  <div>
                    <p className="text-slate-800 font-medium text-sm group-hover:text-green-600 transition-colors">
                      Meeting on {meeting.date}
                    </p>
                    <p className="text-xs text-slate-400 mt-1 line-clamp-1">{meeting.summary || 'Processing...'}</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-sm font-medium" style={{
                    color: meeting.sentiment_score > 0.6 ? '#10b981' : meeting.sentiment_score > 0.4 ? '#f59e0b' : '#f43f5e'
                  }}>
                    {meeting.sentiment_score?.toFixed(2) || 'N/A'}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <p className="text-slate-400 text-center py-8">No meetings recorded yet</p>
        )}
      </div>
    </div>
  );
}

export default EmployeeProfile;
