import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import EmployeeList from './pages/EmployeeList';
import EmployeeProfile from './pages/EmployeeProfile';
import MeetingInsights from './pages/MeetingInsights';
import AIAssistant from './pages/AIAssistant';

function App() {
  return (
    <Router>
      <div className="flex min-h-screen bg-surface-900">
        <Sidebar />
        <main className="flex-1 ml-64 p-8 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/employees" element={<EmployeeList />} />
            <Route path="/employees/:id" element={<EmployeeProfile />} />
            <Route path="/meetings/:id" element={<MeetingInsights />} />
            <Route path="/ai-assistant" element={<AIAssistant />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
