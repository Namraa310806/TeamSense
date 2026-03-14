import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Users, MessageSquare, TrendingUp, AlertTriangle, ArrowUpRight, Activity } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { fetchDashboard } from '../services/api';

const COLORS = ['#22c55e', '#06b6d4', '#10b981', '#f59e0b', '#f43f5e', '#8b5cf6'];

function StatsCard({ icon: Icon, label, value, trend, color }) {
  return (
    <div className="glass-card p-6 stat-glow animate-fade-in">
      <div className="flex items-start justify-between">
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        {trend && (
          <span className="flex items-center gap-1 text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded-full border border-green-100">
            <ArrowUpRight className="w-3 h-3" />
            {trend}
          </span>
        )}
      </div>
      <div className="mt-4">
        <p className="text-3xl font-bold text-slate-800">{value}</p>
        <p className="text-sm text-slate-500 mt-1">{label}</p>
      </div>
    </div>
  );
}

function SentimentTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card p-3 text-xs shadow-lg">
        <p className="text-slate-800 font-medium">{label}</p>
        <p className="text-green-600 mt-1">
          Sentiment: {payload[0].value?.toFixed(2) || 'N/A'}
        </p>
        <p className="text-slate-500">
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
          meeting_intelligence: {
            top_contributors: [
              { employee_id: 1, employee_name: 'Sarah Chen', avg_engagement: 0.87 },
              { employee_id: 3, employee_name: 'Priya Sharma', avg_engagement: 0.81 },
              { employee_id: 5, employee_name: 'Rahul Singh', avg_engagement: 0.76 },
              { employee_id: 7, employee_name: 'Neha Patel', avg_engagement: 0.72 },
              { employee_id: 2, employee_name: 'James Wilson', avg_engagement: 0.66 },
            ],
            low_participation_employees: [
              { employee_id: 8, employee_name: 'Tom Bradley', avg_engagement: 0.29 },
              { employee_id: 4, employee_name: 'Ava Martin', avg_engagement: 0.33 },
            ],
            top_sentiment_people: [
              { employee_id: 3, employee_name: 'Priya Sharma', avg_sentiment: 0.89, meeting_count: 3 },
              { employee_id: 1, employee_name: 'Sarah Chen', avg_sentiment: 0.84, meeting_count: 4 },
              { employee_id: 7, employee_name: 'Neha Patel', avg_sentiment: 0.79, meeting_count: 2 },
              { employee_id: 5, employee_name: 'Rahul Singh', avg_sentiment: 0.74, meeting_count: 2 },
              { employee_id: 6, employee_name: 'Ishita Rao', avg_sentiment: 0.71, meeting_count: 2 },
            ],
          },
        });
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="w-16 h-16 rounded-full border-4 border-green-200 border-t-green-500 animate-spin mx-auto"></div>
          <p className="text-slate-500 mt-4">Loading intelligence data...</p>
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
        <h1 className="text-3xl font-bold text-slate-800">
          Intelligence <span className="gradient-text">Dashboard</span>
        </h1>
        <p className="text-slate-500 mt-2">Real-time HR analytics powered by AI</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          icon={Users}
          label="Total Employees"
          value={data?.employee_count || 0}
          color="from-green-500 to-green-600"
        />
        <StatsCard
          icon={MessageSquare}
          label="Total Meetings"
          value={data?.meeting_count || 0}
          trend="+12%"
          color="from-cyan-500 to-blue-500"
        />
        <StatsCard
          icon={TrendingUp}
          label="Avg Sentiment"
          value={sentimentData.length > 0
            ? (sentimentData.reduce((acc, d) => acc + (d.sentiment || 0), 0) / sentimentData.length).toFixed(2)
            : 'N/A'}
          color="from-emerald-500 to-green-500"
        />
        <StatsCard
          icon={AlertTriangle}
          label="At-Risk Employees"
          value={data?.high_attrition_employees?.length || 0}
          color="from-rose-500 to-red-500"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Department Sentiment Chart */}
        <div className="glass-card p-6 animate-fade-in">
          <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-green-500" />
            Department Sentiment
          </h2>
          {sentimentData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={sentimentData} barSize={40}>
                <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} axisLine={false} tickLine={false} domain={[0, 1]} />
                <Tooltip content={<SentimentTooltip />} cursor={false} />
                <Bar dataKey="sentiment" radius={[8, 8, 0, 0]}>
                  {sentimentData.map((entry, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-slate-400 text-center py-10">No sentiment data available</p>
          )}
        </div>

        {/* Attrition Alerts */}
        <div className="glass-card p-6 animate-fade-in">
          <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-rose-500" />
            Attrition Risk Alerts
          </h2>
          {data?.high_attrition_employees?.length > 0 ? (
            <div className="space-y-3">
              {data.high_attrition_employees.map((emp) => (
                <Link
                  key={emp.id}
                  to={`/employees/${emp.id}`}
                  className="flex items-center justify-between p-4 rounded-xl bg-red-50 hover:bg-red-100 border border-red-100 hover:border-red-200 transition-all group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                      <span className="text-sm font-bold text-red-500">{emp.name.charAt(0)}</span>
                    </div>
                    <div>
                      <p className="text-slate-800 font-medium group-hover:text-red-600 transition-colors">{emp.name}</p>
                      <p className="text-xs text-slate-500">{emp.department}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-red-500 font-bold">{(emp.burnout_risk * 100).toFixed(0)}%</p>
                    <p className="text-xs text-slate-500">Risk Score</p>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-10">
              <div className="w-16 h-16 rounded-full bg-green-50 flex items-center justify-center">
                <TrendingUp className="w-8 h-8 text-green-500" />
              </div>
              <p className="text-green-600 font-medium mt-3">All Clear</p>
              <p className="text-slate-500 text-sm">No high-risk employees detected</p>
            </div>
          )}
        </div>
      </div>

      {/* Meeting Intelligence */}
      <div className="glass-card p-6 animate-fade-in">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Meeting Intelligence</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">Top Contributors</p>
            <div className="space-y-2">
              {(data?.meeting_intelligence?.top_contributors || []).slice(0, 5).map((item) => (
                <div key={item.employee_id} className="flex items-center justify-between bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">
                  <span className="text-sm text-slate-800">{item.employee_name}</span>
                  <span className="text-xs text-emerald-700 font-medium">{Math.round((item.avg_engagement || 0) * 100)}% engagement</span>
                </div>
              ))}
              {(!data?.meeting_intelligence?.top_contributors || data.meeting_intelligence.top_contributors.length === 0) && (
                <p className="text-slate-500 text-sm">No contributor data yet.</p>
              )}
            </div>
          </div>

          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">Top 5 By Sentiment</p>
            <div className="space-y-2">
              {(data?.meeting_intelligence?.top_sentiment_people || []).slice(0, 5).map((item) => (
                <div key={item.employee_id} className="flex items-center justify-between bg-cyan-50 border border-cyan-200 rounded-lg px-3 py-2">
                  <span className="text-sm text-slate-800">{item.employee_name}</span>
                  <span className="text-xs text-cyan-700 font-medium">
                    {Math.round((item.avg_sentiment || 0) * 100)}% sentiment
                  </span>
                </div>
              ))}
              {(!data?.meeting_intelligence?.top_sentiment_people || data.meeting_intelligence.top_sentiment_people.length === 0) && (
                <p className="text-slate-500 text-sm">No sentiment ranking data yet.</p>
              )}
            </div>
          </div>

          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">Low Participation Employees</p>
            <div className="space-y-2">
              {(data?.meeting_intelligence?.low_participation_employees || []).slice(0, 5).map((item) => (
                <div key={item.employee_id} className="flex items-center justify-between bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                  <span className="text-sm text-slate-800">{item.employee_name}</span>
                  <span className="text-xs text-amber-700 font-medium">{Math.round((item.avg_engagement || 0) * 100)}% engagement</span>
                </div>
              ))}
              {(!data?.meeting_intelligence?.low_participation_employees || data.meeting_intelligence.low_participation_employees.length === 0) && (
                <p className="text-slate-500 text-sm">No low-participation data yet.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
