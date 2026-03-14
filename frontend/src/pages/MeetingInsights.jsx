import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, FileText, Hash, TrendingUp, Sparkles } from 'lucide-react';
import { fetchMeeting } from '../services/api';

function MeetingInsights() {
  const { id } = useParams();
  const [meeting, setMeeting] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMeeting(id)
      .then((res) => setMeeting(res.data))
      .catch(() => {
        setMeeting({
          id,
          employee_name: 'Employee',
          date: '2026-03-10',
          transcript: 'Meeting transcript would appear here...',
          summary: 'AI-generated summary would appear here...',
          sentiment_score: 0.72,
          key_topics: [{ topic: 'Career Development', relevance: 0.8 }, { topic: 'Performance', relevance: 0.6 }],
        });
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="w-16 h-16 rounded-full border-4 border-green-200 border-t-green-500 animate-spin"></div>
      </div>
    );
  }

  const sentimentLabel = meeting?.sentiment_score > 0.6 ? 'Positive' : meeting?.sentiment_score > 0.4 ? 'Neutral' : 'Negative';
  const sentimentColor = meeting?.sentiment_score > 0.6 ? 'text-emerald-600' : meeting?.sentiment_score > 0.4 ? 'text-amber-600' : 'text-rose-600';

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Back */}
      <Link to="/employees" className="flex items-center gap-2 text-slate-500 hover:text-slate-800 text-sm transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back
      </Link>

      {/* Header */}
      <div className="glass-card p-6 animate-slide-up">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Meeting Insights</h1>
            <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
              <span>{meeting?.employee_name}</span>
              <span>•</span>
              <span>{meeting?.date}</span>
            </div>
          </div>
          <div className="text-right">
            <div className={`text-3xl font-bold ${sentimentColor}`}>
              {(meeting?.sentiment_score * 100).toFixed(0)}%
            </div>
            <p className={`text-sm font-medium ${sentimentColor}`}>{sentimentLabel}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Summary */}
        <div className="lg:col-span-2 glass-card p-6 animate-fade-in">
          <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-violet-500" />
            AI Summary
          </h2>
          <div className="text-sm text-slate-600 leading-relaxed whitespace-pre-line bg-gray-50 rounded-xl p-4 border border-gray-200">
            {meeting?.summary || 'Summary not generated yet.'}
          </div>
        </div>

        {/* Topics & Sentiment */}
        <div className="space-y-6">
          {/* Topics */}
          <div className="glass-card p-6 animate-fade-in">
            <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
              <Hash className="w-5 h-5 text-cyan-500" />
              Key Topics
            </h2>
            <div className="space-y-3">
              {(meeting?.key_topics || []).map((topic, i) => (
                <div key={i} className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">{topic.topic || topic}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 h-1.5 rounded-full bg-gray-200 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-green-500 to-green-400"
                        style={{ width: `${(topic.relevance || 0.5) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-slate-400">{((topic.relevance || 0.5) * 100).toFixed(0)}%</span>
                  </div>
                </div>
              ))}
              {(!meeting?.key_topics || meeting.key_topics.length === 0) && (
                <p className="text-slate-400 text-sm">No topics extracted</p>
              )}
            </div>
          </div>

          {/* Sentiment Gauge */}
          <div className="glass-card p-6 animate-fade-in">
            <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-500" />
              Emotion Analysis
            </h2>
            <div className="space-y-3">
              <div className="sentiment-bar">
                <div
                  className="absolute top-1/2 transform -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-md border-2 border-green-500 transition-all"
                  style={{ left: `${(meeting?.sentiment_score || 0.5) * 100}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-slate-400">
                <span>Negative</span>
                <span>Neutral</span>
                <span>Positive</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Full Transcript */}
      <div className="glass-card p-6 animate-fade-in">
        <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-slate-400" />
          Full Transcript
        </h2>
        <div className="text-sm text-slate-500 leading-relaxed bg-gray-50 rounded-xl p-4 border border-gray-200 max-h-96 overflow-y-auto">
          {meeting?.transcript || 'No transcript available.'}
        </div>
      </div>
    </div>
  );
}

export default MeetingInsights;
