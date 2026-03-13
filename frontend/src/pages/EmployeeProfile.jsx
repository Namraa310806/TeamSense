import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, User, Briefcase, Calendar, Mail, TrendingUp, AlertTriangle, MessageSquare, Brain, Target, AlertCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { fetchEmployee, fetchAttrition, uploadMeeting } from '../services/api';

function EmployeeProfile() {
  const { id } = useParams();
  const [employee, setEmployee] = useState(null);
  const [attrition, setAttrition] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    Promise.all([
      fetchEmployee(id).then((r) => r.data).catch(() => null),
      fetchAttrition(id).then((r) => r.data).catch(() => null),
    ]).then(([empData, attrData]) => {
      setEmployee(empData || {
        id, name: 'Employee', role: 'Role', department: 'Department',
        join_date: '2024-01-15', manager: 'Manager', email: 'employee@teamsense.ai',
        meetings: [], insights: null, meeting_count: 0, avg_sentiment: 0.65,
      });
      setAttrition(attrData || { risk_score: 0.3, risk_level: 'low', factors: ['No data'] });
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
      // Reload data
      const res = await fetchEmployee(id);
      setEmployee(res.data);
    } catch (err) {
      console.error('Upload failed:', err);
    }
    setUploading(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="w-16 h-16 rounded-full border-4 border-primary-500/30 border-t-primary-500 animate-spin"></div>
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
    critical: 'text-red-400 bg-red-500/10 border-red-500/30',
    high: 'text-accent-rose bg-accent-rose/10 border-accent-rose/30',
    medium: 'text-accent-amber bg-accent-amber/10 border-accent-amber/30',
    low: 'text-accent-emerald bg-accent-emerald/10 border-accent-emerald/30',
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Back & Header */}
      <div className="animate-slide-up">
        <Link to="/employees" className="flex items-center gap-2 text-slate-400 hover:text-white text-sm mb-4 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Employees
        </Link>
        <div className="glass-card p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-5">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-accent-cyan flex items-center justify-center">
                <span className="text-2xl font-bold text-white">{employee?.name?.charAt(0)}</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">{employee?.name}</h1>
                <div className="flex items-center gap-4 mt-2 text-sm text-slate-400">
                  <span className="flex items-center gap-1"><Briefcase className="w-4 h-4" />{employee?.role}</span>
                  <span className="flex items-center gap-1"><User className="w-4 h-4" />{employee?.department}</span>
                  <span className="flex items-center gap-1"><Calendar className="w-4 h-4" />Joined {employee?.join_date}</span>
                </div>
                {employee?.email && (
                  <p className="flex items-center gap-1 text-xs text-slate-500 mt-1">
                    <Mail className="w-3 h-3" />{employee.email}
                  </p>
                )}
              </div>
            </div>
            <button
              onClick={() => setShowUpload(!showUpload)}
              className="px-4 py-2 bg-gradient-to-r from-primary-600 to-primary-500 text-white rounded-xl text-sm font-medium hover:shadow-lg hover:shadow-primary-500/20 transition-all"
            >
              Upload Meeting
            </button>
          </div>
        </div>
      </div>

      {/* Upload form */}
      {showUpload && (
        <div className="glass-card p-6 animate-slide-up">
          <h3 className="text-white font-semibold mb-3">Upload Meeting Transcript</h3>
          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="Paste the meeting transcript here..."
            className="w-full h-40 bg-surface-900/50 border border-surface-700 rounded-xl p-4 text-white text-sm resize-none focus:border-primary-500 focus:outline-none transition-colors"
          />
          <div className="flex gap-3 mt-3">
            <button
              onClick={handleUpload}
              disabled={uploading || !transcript.trim()}
              className="px-6 py-2.5 bg-primary-600 hover:bg-primary-500 text-white rounded-xl text-sm font-medium disabled:opacity-50 transition-colors"
            >
              {uploading ? 'Processing...' : 'Upload & Analyze'}
            </button>
            <button onClick={() => setShowUpload(false)} className="px-6 py-2.5 bg-surface-700 text-slate-300 rounded-xl text-sm transition-colors">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Sentiment Chart */}
        <div className="glass-card p-6 md:col-span-2 animate-fade-in">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary-400" />
            Sentiment Trend
          </h2>
          {sentimentData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={sentimentData}>
                <defs>
                  <linearGradient id="sentimentGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#818cf8" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#818cf8" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 1]} tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: 'rgba(30, 41, 59, 0.9)', border: '1px solid rgba(99, 102, 241, 0.2)', borderRadius: '12px', fontSize: '12px' }}
                  labelStyle={{ color: '#e2e8f0' }}
                />
                <Area type="monotone" dataKey="sentiment" stroke="#818cf8" fill="url(#sentimentGradient)" strokeWidth={2} dot={{ fill: '#818cf8', r: 4 }} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-slate-500 text-center py-10">No sentiment data yet</p>
          )}
        </div>

        {/* Attrition Risk */}
        <div className="glass-card p-6 animate-fade-in">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-accent-amber" />
            Attrition Risk
          </h2>
          {attrition && (
            <div className="text-center">
              <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full border font-semibold text-sm ${riskColor[attrition.risk_level] || riskColor.low}`}>
                {attrition.risk_level?.toUpperCase()}
              </div>
              <div className="mt-4">
                <div className="text-4xl font-bold text-white">{(attrition.risk_score * 100).toFixed(0)}%</div>
                <p className="text-xs text-slate-500 mt-1">Risk Score</p>
              </div>
              <div className="mt-4 space-y-2">
                {attrition.factors?.map((f, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-slate-400">
                    <AlertCircle className="w-3 h-3 mt-0.5 text-accent-amber flex-shrink-0" />
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
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Brain className="w-5 h-5 text-accent-violet" />
            AI Insights
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h3 className="text-sm font-medium text-slate-400 mb-2 flex items-center gap-1">
                <Target className="w-4 h-4" /> Topics
              </h3>
              <div className="flex flex-wrap gap-2">
                {(insights.topics || []).map((t, i) => (
                  <span key={i} className="text-xs px-3 py-1.5 rounded-full bg-primary-500/10 text-primary-300 border border-primary-500/20">
                    {t.topic || t}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-sm font-medium text-slate-400 mb-2">Career Goals</h3>
              <p className="text-sm text-white">{insights.career_goals || 'Not identified yet'}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-slate-400 mb-2">Concerns</h3>
              <p className="text-sm text-white">{insights.concerns || 'No concerns flagged'}</p>
            </div>
          </div>
        </div>
      )}

      {/* Meeting Timeline */}
      <div className="glass-card p-6 animate-fade-in">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-accent-cyan" />
          Meeting Timeline
        </h2>
        {meetings.length > 0 ? (
          <div className="space-y-3">
            {meetings.map((meeting) => (
              <Link
                key={meeting.id}
                to={`/meetings/${meeting.id}`}
                className="flex items-center justify-between p-4 rounded-xl bg-surface-900/50 hover:bg-surface-700/50 border border-surface-700/50 hover:border-primary-500/20 transition-all group"
              >
                <div className="flex items-center gap-4">
                  <div className="w-2 h-2 rounded-full" style={{
                    backgroundColor: meeting.sentiment_score > 0.6 ? '#10b981' : meeting.sentiment_score > 0.4 ? '#f59e0b' : '#f43f5e'
                  }} />
                  <div>
                    <p className="text-white font-medium text-sm group-hover:text-primary-300 transition-colors">
                      Meeting on {meeting.date}
                    </p>
                    <p className="text-xs text-slate-500 mt-1 line-clamp-1">{meeting.summary || 'Processing...'}</p>
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
          <p className="text-slate-500 text-center py-8">No meetings recorded yet</p>
        )}
      </div>
    </div>
  );
}

export default EmployeeProfile;
