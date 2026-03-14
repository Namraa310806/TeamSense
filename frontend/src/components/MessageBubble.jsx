function MessageBubble({ role, text }) {
  const isUser = role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? 'bg-green-600 text-white rounded-br-md'
            : 'bg-white border border-gray-200 text-slate-700 rounded-bl-md'
        }`}
      >
        {text}
      </div>
    </div>
  );
}

export default MessageBubble;
