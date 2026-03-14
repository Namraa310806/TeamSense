import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import EmployeeList from './pages/EmployeeList';
import EmployeeProfile from './pages/EmployeeProfile';
import MeetingInsights from './pages/MeetingInsights';
import AIAssistant from './pages/AIAssistant';
import IngestionDashboard from './pages/IngestionDashboard';
import Login from './pages/Login';
import MeetingAnalysis from './pages/MeetingAnalysis';
import Register from './pages/Register';
import HRManagement from './pages/HRManagement';
import AIAssistantWidget from './components/AIAssistantWidget';
import GlobalToast from './components/GlobalToast';

function isLikelyJwt(token) {
  return typeof token === 'string' && token.split('.').length === 3;
}

function isJwtExpired(token) {
  try {
    const payloadBase64 = token.split('.')[1];
    const payloadJson = atob(payloadBase64.replace(/-/g, '+').replace(/_/g, '/'));
    const payload = JSON.parse(payloadJson);
    if (!payload.exp) return false;
    return Date.now() >= Number(payload.exp) * 1000;
  } catch {
    return true;
  }
}

/** Returns true when the user has a valid session stored in localStorage. */
function isAuthenticated() {
  try {
    const user = localStorage.getItem('user');
    const token = localStorage.getItem('access_token');
    if (!user || !token) return false;
    if (!isLikelyJwt(token)) return false;
    if (isJwtExpired(token)) {
      localStorage.removeItem('user');
      localStorage.removeItem('access_token');
      return false;
    }
    return true;
  } catch {
    return false;
  }
}

/** Returns the role of the logged-in user from localStorage. */
function getUserRole() {
  try {
    const raw = localStorage.getItem('user');
    if (raw) return JSON.parse(raw)?.role || null;
  } catch {
    return null;
  }
  return null;
}

/** Wraps a route so it redirects to /login when the user is not authenticated. */
function ProtectedRoute({ children }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

/** Wraps a route so it only allows CHR users; others are sent to /. */
function CHRProtectedRoute({ children }) {
  if (!isAuthenticated()) return <Navigate to="/login" replace />;
  if (getUserRole() !== 'CHR') return <Navigate to="/" replace />;
  return children;
}

/** Layout wrapper that renders the sidebar + main content area. */
function AppLayout({ children }) {
  return (
    <div className="flex min-h-screen bg-green-50">
      <Sidebar />
      <main className="flex-1 ml-64 p-8 overflow-auto bg-green-50">
        {children}
      </main>
      <AIAssistantWidget />
      <GlobalToast />
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        {/* Public route – full screen, no sidebar */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Protected routes – require authentication, rendered inside AppLayout */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout><Dashboard /></AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/employees"
          element={
            <ProtectedRoute>
              <AppLayout><EmployeeList /></AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/employees/:id"
          element={
            <ProtectedRoute>
              <AppLayout><EmployeeProfile /></AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/meetings/:id"
          element={
            <ProtectedRoute>
              <AppLayout><MeetingInsights /></AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/ai-assistant"
          element={
            <ProtectedRoute>
              <AppLayout><AIAssistant /></AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/meeting-analysis"
          element={
            <ProtectedRoute>
              <AppLayout><MeetingAnalysis /></AppLayout>
            </ProtectedRoute>
          }
        />

        {/* CHR-only route – non-CHR users redirected to / */}
        <Route
          path="/hr-management"
          element={
            <CHRProtectedRoute>
              <AppLayout><HRManagement /></AppLayout>
            </CHRProtectedRoute>
          }
        />
        <Route
          path="/ingestion"
          element={
            <ProtectedRoute>
              <AppLayout><IngestionDashboard /></AppLayout>
            </ProtectedRoute>
          }
        />

        {/* Catch-all: redirect to dashboard (ProtectedRoute handles auth check) */}
        <Route path="*" element={<Navigate to="/" replace />} />

      </Routes>
    </Router>
  );
}

export default App;
