import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import EmployeeList from './pages/EmployeeList';
import EmployeeProfile from './pages/EmployeeProfile';
import MeetingInsights from './pages/MeetingInsights';
import AIAssistant from './pages/AIAssistant';
import Login from './pages/Login';

/** Returns true when the user has a valid session stored in localStorage. */
function isAuthenticated() {
  try {
    const user = localStorage.getItem('user');
    const token = localStorage.getItem('access_token');
    return !!(user && token);
  } catch {
    return false;
  }
}

/** Wraps a route so it redirects to /login when the user is not authenticated. */
function ProtectedRoute({ children }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

/** Layout wrapper that renders the sidebar + main content area. */
function AppLayout({ children }) {
  return (
    <div className="flex min-h-screen bg-surface-900">
      <Sidebar />
      <main className="flex-1 ml-64 p-8 overflow-auto">
        {children}
      </main>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        {/* Public route – full screen, no sidebar */}
        <Route path="/login" element={<Login />} />

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

        {/* Catch-all: redirect to dashboard (ProtectedRoute handles auth check) */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
