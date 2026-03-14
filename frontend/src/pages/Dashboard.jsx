import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Users, MessageSquare, TrendingUp, AlertTriangle, ArrowUpRight, Activity } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { fetchDashboard } from '../services/api';

const COLORS = ['#818cf8', '#06b6d4', '#10b981', '#f59e0b', '#f43f5e', '#8b5cf6'];

function StatsCard({ icon: Icon, label, value, trend, color }) {
  return (
    <div className="glass-card p-6 stat-glow animate-fade-in">
      <div className="flex items-start justify-between">
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        {trend && (
          <span className="flex items-center gap-1 text-xs font-medium text-accent-emerald bg-accent-emerald/10 px-2 py-1 rounded-full">
            <ArrowUpRight className="w-3 h-3" />
            {trend}
          </span>
        )}
      </div>
      <div className="mt-4">
        <p className="text-3xl font-bold text-white">{value}</p>
        <p className="text-sm text-slate-400 mt-1">{label}</p>
      </div>
    </div>
  );
}

function SentimentTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card p-3 text-xs">
        <p className="text-white font-medium">{label}</p>
        <p className="text-primary-300 mt-1">
          Sentiment: {payload[0].value?.toFixed(2) || 'N/A'}
        </p>
        <p className="text-slate-400">
          {payload[0].payload.meeting_count} meetings
        </p>
      </div>
    );
  }
  return null;
}

function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard()
      .then((res) => setData(res.data))
      .catch((err) => {
        console.error('Dashboard fetch error:', err);
        // Set mock data for development
        setData({
          employee_count: 8,
          meeting_count: 8,
          department_sentiment: [
            { department: 'Engineering', avg_sentiment: 0.62, meeting_count: 5 },
            { department: 'Data Science', avg_sentiment: 0.32, meeting_count: 1 },
            { department: 'Sales', avg_sentiment: 0.45, meeting_count: 1 },
            { department: 'Mobile', avg_sentiment: 0.82, meeting_count: 1 },
          ],
          high_attrition_employees: [
            { id: 2, name: 'James Wilson', department: 'Data Science', burnout_risk: 0.68 },
            { id: 8, name: 'Tom Bradley', department: 'Engineering', burnout_risk: 0.82 },
          ],
          recent_meetings: [
            { id: 1, employee_name: 'Sarah Chen', date: '2026-03-10', sentiment_score: 0.78 },
            { id: 2, employee_name: 'James Wilson', date: '2026-03-09', sentiment_score: 0.32 },
            { id: 3, employee_name: 'Priya Sharma', date: '2026-03-08', sentiment_score: 0.89 },
          ],
        });
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="w-16 h-16 rounded-full border-4 border-primary-500/30 border-t-primary-500 animate-spin mx-auto"></div>
          <p className="text-slate-400 mt-4">Loading intelligence data...</p>
        </div>
      </div>
    );
  }

  const sentimentData = data?.department_sentiment?.map((d) => ({
    ...d,
    name: d.department,
    sentiment: d.avg_sentiment,
  })) || [];

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="animate-slide-up">
        <h1 className="text-3xl font-bold text-white">
          Intelligence <span className="gradient-text">Dashboard</span>
        </h1>
        <p className="text-slate-400 mt-2">Real-time HR analytics powered by AI</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          icon={Users}
          label="Total Employees"
          value={data?.employee_count || 0}
          color="from-primary-500 to-primary-700"
        />
        <StatsCard
          icon={MessageSquare}
          label="Total Meetings"
          value={data?.meeting_count || 0}
          trend="+12%"
          color="from-accent-cyan to-blue-600"
        />
        <StatsCard
          icon={TrendingUp}
          label="Avg Sentiment"
          value={sentimentData.length > 0
            ? (sentimentData.reduce((acc, d) => acc + (d.sentiment || 0), 0) / sentimentData.length).toFixed(2)
            : 'N/A'}
          color="from-accent-emerald to-green-600"
        />
        <StatsCard
          icon={AlertTriangle}
          label="At-Risk Employees"
          value={data?.high_attrition_employees?.length || 0}
          color="from-accent-rose to-red-600"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Department Sentiment Chart */}
        <div className="glass-card p-6 animate-fade-in">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary-400" />
            Department Sentiment
          </h2>
          {sentimentData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={sentimentData} barSize={40}>
                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} domain={[0, 1]} />
                <Tooltip content={<SentimentTooltip />} cursor={false} />
                <Bar dataKey="sentiment" radius={[8, 8, 0, 0]}>
                  {sentimentData.map((entry, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-slate-500 text-center py-10">No sentiment data available</p>
          )}
        </div>

        {/* Attrition Alerts */}
        <div className="glass-card p-6 animate-fade-in">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-accent-rose" />
            Attrition Risk Alerts
          </h2>
          {data?.high_attrition_employees?.length > 0 ? (
            <div className="space-y-3">
              {data.high_attrition_employees.map((emp) => (
                <Link
                  key={emp.id}
                  to={`/employees/${emp.id}`}
                  className="flex items-center justify-between p-4 rounded-xl bg-surface-900/50 hover:bg-surface-700/50 border border-accent-rose/10 hover:border-accent-rose/30 transition-all group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-accent-rose/20 to-accent-amber/20 flex items-center justify-center">
                      <span className="text-sm font-bold text-accent-rose">{emp.name.charAt(0)}</span>
                    </div>
                    <div>
                      <p className="text-white font-medium group-hover:text-accent-rose transition-colors">{emp.name}</p>
                      <p className="text-xs text-slate-500">{emp.department}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-accent-rose font-bold">{(emp.burnout_risk * 100).toFixed(0)}%</p>
                    <p className="text-xs text-slate-500">Risk Score</p>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-10">
              <div className="w-16 h-16 rounded-full bg-accent-emerald/10 flex items-center justify-center">
                <TrendingUp className="w-8 h-8 text-accent-emerald" />
              </div>
              <p className="text-accent-emerald font-medium mt-3">All Clear</p>
              <p className="text-slate-500 text-sm">No high-risk employees detected</p>
            </div>
          )}
        </div>
      </div>

      {/* Recent Meetings */}
      <div className="glass-card p-6 animate-fade-in">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-accent-cyan" />
          Recent Meetings
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-surface-700">
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 uppercase tracking-wider">Employee</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 uppercase tracking-wider">Date</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 uppercase tracking-wider">Sentiment</th>
                <th className="text-right py-3 px-4 text-xs font-medium text-slate-500 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody>
              {data?.recent_meetings?.map((meeting) => (
                <tr key={meeting.id} className="border-b border-surface-700/50 hover:bg-surface-700/30 transition-colors">
                  <td className="py-3 px-4">
                    <span className="text-white font-medium">{meeting.employee_name}</span>
                  </td>
                  <td className="py-3 px-4 text-slate-400 text-sm">{meeting.date}</td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 rounded-full bg-surface-700 overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${(meeting.sentiment_score || 0) * 100}%`,
                            backgroundColor: meeting.sentiment_score > 0.6 ? '#10b981' : meeting.sentiment_score > 0.4 ? '#f59e0b' : '#f43f5e',
                          }}
                        />
                      </div>
                      <span className="text-xs text-slate-400">{meeting.sentiment_score?.toFixed(2)}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <Link to={`/meetings/${meeting.id}`} className="text-primary-400 hover:text-primary-300 text-sm font-medium transition-colors">
                      View →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
