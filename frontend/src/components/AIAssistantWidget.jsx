import { useState } from 'react';
import { MessageCircle } from 'lucide-react';
import ChatWindow from './ChatWindow';

function AIAssistantWidget() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        className="ai-widget-fab"
        onClick={() => setOpen((prev) => !prev)}
        aria-label="Open HR AI assistant"
        title="HR AI Assistant"
      >
        <MessageCircle className="w-6 h-6" />
      </button>

      <ChatWindow
        isOpen={open}
        onClose={() => setOpen(false)}
        onMinimize={() => setOpen(false)}
      />
    </>
  );
}

export default AIAssistantWidget;
