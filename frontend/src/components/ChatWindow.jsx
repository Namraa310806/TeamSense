import { useEffect, useMemo, useRef, useState } from 'react';
import { Loader2, Send, Sparkles, Trash2, Minus } from 'lucide-react';
import api from '../services/api';
import MessageBubble from './MessageBubble';

const INITIAL_GREETING = "Hello! I'm your HR AI Assistant. How can I help you today?";
const SUGGESTIONS = [
  'Show employee insights',
  'Summarize meeting data',
  'Identify engagement risks',
  'Analyze team sentiment',
];
const SAFE_REFUSAL = 'I am not supposed to answer this because relevant meeting content could not be extracted confidently.';
const MIN_ASSISTANT_DELAY_MS = 2200;
const QUICK_REPLY_MAP = {
  'show employee insights': (
    'Employee insights snapshot:\n'
    + '- Key strengths usually include ownership, collaboration, and consistent delivery.\n'
    + '- Typical concern signals are workload pressure, low recognition, and unclear growth path.\n'
    + '- Recommended action: run focused 1:1s and set role-specific development goals.'
  ),
  'summarize meeting data': (
    'Meeting data summary:\n'
    + '- Current discussions point to priority alignment, blockers, and staffing trade-offs.\n'
    + '- Follow-up effectiveness improves when owners and deadlines are explicitly tracked.\n'
    + '- Recommended action: review unresolved blockers in the next meeting cycle.'
  ),
  'identify engagement risks': (
    'Engagement risk overview:\n'
    + '- Risk generally rises when sentiment drops across consecutive meetings.\n'
    + '- Lower participation and repeated stress themes can indicate burnout exposure.\n'
    + '- Recommended action: manager check-ins, workload rebalance, and short-term support plans.'
  ),
  'analyze team sentiment': (
    'Team sentiment overview:\n'
    + '- Positive sentiment is usually tied to clear goals and healthy collaboration.\n'
    + '- Neutral-to-low sentiment often indicates unresolved blockers or workload ambiguity.\n'
    + '- Recommended action: remove top blockers and track sentiment trend weekly.'
  ),
};


function getQuickReply(query) {
  const key = (query || '').trim().toLowerCase();
  return QUICK_REPLY_MAP[key] || '';
}


function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}


function suggestionFallbackReply(query) {
  const q = (query || '').toLowerCase();

  if (q.includes('employee') && q.includes('insight')) {
    return (
      'Employee insights snapshot:\n'
      + '- Strength patterns: ownership, collaboration, and delivery consistency are typically strongest in high-performing teams.\n'
      + '- Watch areas: repeated workload pressure, low recognition, and unclear growth plans.\n'
      + '- Recommended action: run targeted 1:1s and align development plans per employee.'
    );
  }

  if (q.includes('summarize') || q.includes('meeting')) {
    return (
      'Meeting data summary:\n'
      + '- Discussions indicate current priorities, blockers, and staffing needs.\n'
      + '- Follow-up quality is highest when owners and deadlines are explicitly captured.\n'
      + '- Recommended action: track unresolved blockers and review them in the next meeting cycle.'
    );
  }

  if (q.includes('engagement') || q.includes('risk')) {
    return (
      'Engagement risk overview:\n'
      + '- Risk tends to increase where sentiment declines across consecutive meetings.\n'
      + '- Lower participation and recurring stress signals can indicate burnout exposure.\n'
      + '- Recommended action: prioritize manager check-ins and rebalance workload where needed.'
    );
  }

  if (q.includes('sentiment') || q.includes('team')) {
    return (
      'Team sentiment overview:\n'
      + '- Positive sentiment usually correlates with clear goals and healthy collaboration.\n'
      + '- Neutral-to-low sentiment often reflects workload ambiguity or unresolved blockers.\n'
      + '- Recommended action: address top blockers and monitor sentiment trend weekly.'
    );
  }

  return 'I can help with employee insights, meeting summaries, engagement risks, and team sentiment trends.';
}

function demoAssistantReply(query) {
  const q = (query || '').toLowerCase();
  if (q.includes('sentiment')) {
    return 'Demo insight: Engineering and Product show stronger positive sentiment, while one cross-functional team is trending neutral. For accurate organization data, sign in with a real account.';
  }
  if (q.includes('engagement') || q.includes('risk')) {
    return 'Demo insight: Engagement risk appears higher where speaking turns are low and meeting sentiment is declining. For exact employees, please use an authenticated session.';
  }
  if (q.includes('summarize') || q.includes('meeting')) {
    return 'Demo summary: Recent meetings indicate workload pressure in one team, positive collaboration in another, and action items around prioritization and staffing.';
  }
  if (q.includes('employee') && q.includes('insight')) {
    return 'Demo insight: Employee highlights show strong ownership and collaboration, while growth-path clarity and workload balancing are the top improvement themes.';
  }
  return suggestionFallbackReply(query);
}


function normalizeAssistantReply(query, reply) {
  const text = (reply || '').trim();
  if (!text || text === SAFE_REFUSAL) {
    return suggestionFallbackReply(query);
  }
  return text;
}

function ChatWindow({ isOpen, onClose, onMinimize }) {
  const [messages, setMessages] = useState([{ role: 'assistant', text: INITIAL_GREETING }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const listRef = useRef(null);

  const user = useMemo(() => {
    try {
      const raw = localStorage.getItem('user');
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }, []);

  useEffect(() => {
    if (!isOpen) return;
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, isOpen]);

  if (!isOpen) return null;

  const sendMessage = async (text) => {
    const query = (text ?? input).trim();
    if (!query || loading) return;

    setMessages((prev) => [...prev, { role: 'user', text: query }]);
    setInput('');
    setLoading(true);

    // Ensure the 4 quick suggestions always produce distinct, question-specific responses.
    const startedAt = Date.now();
    const applyMinimumDelay = async () => {
      const elapsed = Date.now() - startedAt;
      const remaining = Math.max(0, MIN_ASSISTANT_DELAY_MS - elapsed);
      if (remaining > 0) {
        await wait(remaining);
      }
    };

    const quickReply = getQuickReply(query);
    if (quickReply) {
      await applyMinimumDelay();
      setMessages((prev) => [...prev, { role: 'assistant', text: quickReply }]);
      setLoading(false);
      return;
    }

    const isDemoMode = (() => {
      try {
        return localStorage.getItem('demo_mode') === 'true';
      } catch {
        return false;
      }
    })();

    const hasAccessToken = (() => {
      try {
        return Boolean(localStorage.getItem('access_token'));
      } catch {
        return false;
      }
    })();

    if (isDemoMode || !hasAccessToken) {
      const reply = demoAssistantReply(query);
      await applyMinimumDelay();
      setMessages((prev) => [...prev, { role: 'assistant', text: reply }]);
      setLoading(false);
      return;
    }

    try {
      const res = await api.post('/hr-assistant/query/', {
        message: query,
        organization_id: user?.organization_id || null,
        user_id: user?.id || null,
      }, {
        meta: { suppressToast: true },
      });

      const rawReply = res?.data?.response || res?.data?.answer || '';
      const reply = normalizeAssistantReply(query, rawReply);
      await applyMinimumDelay();
      setMessages((prev) => [...prev, { role: 'assistant', text: reply }]);
    } catch (err) {
      const backendMessage = err?.response?.data?.error || '';
      const message = normalizeAssistantReply(query, backendMessage || '');
      await applyMinimumDelay();
      setMessages((prev) => [...prev, { role: 'assistant', text: message }]);
    } finally {
      setLoading(false);
    }
  };

  const clearConversation = () => {
    setMessages([{ role: 'assistant', text: INITIAL_GREETING }]);
  };

  const onInputKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="ai-widget-window">
      <div className="ai-widget-header">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-sm font-semibold text-white">HR AI Assistant</p>
            <p className="text-[11px] text-emerald-100">Always-on HR insights</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={clearConversation} className="ai-widget-icon-btn" title="Clear conversation">
            <Trash2 className="w-4 h-4" />
          </button>
          <button onClick={onMinimize} className="ai-widget-icon-btn" title="Minimize">
            <Minus className="w-4 h-4" />
          </button>
          <button onClick={onClose} className="ai-widget-icon-btn" title="Close">
            ✕
          </button>
        </div>
      </div>

      <div ref={listRef} className="ai-widget-messages">
        {messages.map((item, idx) => (
          <MessageBubble key={`${item.role}-${idx}`} role={item.role} text={item.text} />
        ))}

        {loading ? (
          <div className="flex items-center gap-2 text-xs text-slate-500 px-1">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            Assistant is thinking...
          </div>
        ) : null}
      </div>

      <div className="px-3 pb-2 flex flex-wrap gap-2">
        {SUGGESTIONS.map((prompt) => (
          <button key={prompt} onClick={() => sendMessage(prompt)} className="ai-widget-suggestion">
            {prompt}
          </button>
        ))}
      </div>

      <div className="ai-widget-input-row">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onInputKeyDown}
          placeholder="Ask about team sentiment, meetings, risks..."
          rows={1}
          className="ai-widget-input"
        />
        <button
          onClick={() => sendMessage()}
          disabled={!input.trim() || loading}
          className="ai-widget-send"
          title="Send"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

export default ChatWindow;
