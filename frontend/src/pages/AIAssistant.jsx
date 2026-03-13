import { useState, useRef, useEffect } from 'react';
import { Send, Brain, User, Sparkles, BookOpen, Loader2 } from 'lucide-react';
import { aiQuery } from '../services/api';

const SUGGESTIONS = [
  "What are the common concerns across employees?",
  "Who has showing declining sentiment recently?",
  "What career goals have been mentioned in meetings?",
  "Summarize recent meeting highlights",
  "Which employees might be at risk of burnout?",
];

function AIAssistant() {
  const [messages, setMessages] = useState([
    {
      role: 'ai',
      content: "Hello! I'm TeamSense AI, your HR intelligence assistant. I can help you analyze employee meeting data, find insights, and answer questions about your team. What would you like to know?",
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (query = input) => {
    if (!query.trim() || loading) return;

    const userMessage = { role: 'user', content: query };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const res = await aiQuery(query);
      const data = res.data;

      let aiContent = data.answer || 'I found some relevant information but could not generate a specific answer.';

      if (data.sources && data.sources.length > 0) {
        aiContent += '\n\n📎 Sources:';
        data.sources.forEach((s) => {
          aiContent += `\n• ${s.employee_name} — ${s.date} (${(s.similarity * 100).toFixed(0)}% match)`;
        });
      }

      setMessages((prev) => [...prev, { role: 'ai', content: aiContent }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'ai',
          content: 'I apologize, but I encountered an error processing your query. This might be because the backend server is not running or there are no meeting transcripts uploaded yet. Please try again later.',
        },
      ]);
    }

    setLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-4rem)] flex flex-col">
      {/* Header */}
      <div className="animate-slide-up mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent-violet to-primary-500 flex items-center justify-center">
            <Brain className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">
              AI <span className="gradient-text">Assistant</span>
            </h1>
            <p className="text-sm text-slate-400">Ask anything about your team's meeting data</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2 mb-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex items-start gap-3 animate-slide-up ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${
              msg.role === 'ai'
                ? 'bg-gradient-to-br from-accent-violet to-primary-500'
                : 'bg-gradient-to-br from-primary-600 to-primary-400'
            }`}>
              {msg.role === 'ai' ? <Sparkles className="w-4 h-4 text-white" /> : <User className="w-4 h-4 text-white" />}
            </div>
            <div className={`chat-bubble rounded-2xl px-5 py-3 ${
              msg.role === 'ai' ? 'chat-bubble-ai' : 'chat-bubble-user'
            }`}>
              <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-line">{msg.content}</p>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-start gap-3 animate-fade-in">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-accent-violet to-primary-500 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div className="chat-bubble chat-bubble-ai rounded-2xl px-5 py-3">
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing meeting data...
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions */}
      {messages.length <= 1 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {SUGGESTIONS.map((s, i) => (
            <button
              key={i}
              onClick={() => handleSend(s)}
              className="flex items-center gap-1.5 text-xs px-3 py-2 rounded-xl bg-surface-800/50 border border-surface-700 text-slate-400 hover:text-white hover:border-primary-500/30 transition-all"
            >
              <BookOpen className="w-3 h-3" />
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="glass-card p-3 flex items-end gap-3">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your team..."
          rows={1}
          className="flex-1 bg-transparent border-none text-white text-sm resize-none focus:outline-none placeholder-slate-500 max-h-32"
          style={{ minHeight: '40px' }}
        />
        <button
          onClick={() => handleSend()}
          disabled={!input.trim() || loading}
          className="w-10 h-10 rounded-xl bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 text-white flex items-center justify-center disabled:opacity-50 transition-all shadow-lg shadow-primary-500/20"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

export default AIAssistant;
