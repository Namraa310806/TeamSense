import { useEffect, useState } from 'react';
import { CheckCircle2, AlertCircle } from 'lucide-react';
import { TOAST_EVENT } from '../utils/toast';

function GlobalToast() {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    const onToast = (event) => {
      const detail = event?.detail || {};
      const id = `${Date.now()}-${Math.random()}`;
      const message = String(detail.message || '').trim();
      const type = detail.type === 'error' ? 'error' : 'success';
      const duration = Number(detail.duration) > 0 ? Number(detail.duration) : 2000;

      if (!message) return;

      setToasts((prev) => [...prev, { id, message, type }]);
      window.setTimeout(() => {
        setToasts((prev) => prev.filter((toast) => toast.id !== id));
      }, duration);
    };

    window.addEventListener(TOAST_EVENT, onToast);
    return () => window.removeEventListener(TOAST_EVENT, onToast);
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div className="global-toast-container" aria-live="polite" aria-atomic="true">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`global-toast ${toast.type === 'error' ? 'global-toast-error' : 'global-toast-success'}`}
          role="status"
        >
          {toast.type === 'error' ? (
            <AlertCircle className="w-4 h-4" />
          ) : (
            <CheckCircle2 className="w-4 h-4" />
          )}
          <span>{toast.message}</span>
        </div>
      ))}
    </div>
  );
}

export default GlobalToast;
