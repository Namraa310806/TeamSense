export const TOAST_EVENT = 'teamsense:toast';

export function showToast(message, type = 'success', duration = 2000) {
  if (!message) return;
  window.dispatchEvent(
    new CustomEvent(TOAST_EVENT, {
      detail: {
        message,
        type,
        duration,
      },
    }),
  );
}
