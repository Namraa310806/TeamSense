import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Search, Plus, Users, TrendingUp, ChevronRight, MessageSquare } from 'lucide-react';
import { fetchEmployees, createEmployee } from '../services/api';

function EmployeeList() {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showAdd, setShowAdd] = useState(false);
  const [newEmployee, setNewEmployee] = useState({ name: '', role: '', department: '', email: '', manager: '', join_date: '' });

  useEffect(() => {
    loadEmployees();
  }, []);

  const loadEmployees = () => {
    fetchEmployees()
      .then((res) => {
        const data = res.data.results || res.data;
        setEmployees(Array.isArray(data) ? data : []);
      })
      .catch(() => {
        setEmployees([
          { id: 1, name: 'Sarah Chen', role: 'Senior Engineer', department: 'Engineering', avg_sentiment: 0.78, meeting_count: 3 },
          { id: 2, name: 'James Wilson', role: 'Data Scientist', department: 'Data Science', avg_sentiment: 0.32, meeting_count: 2 },
          { id: 3, name: 'Priya Sharma', role: 'Staff Engineer', department: 'Engineering', avg_sentiment: 0.89, meeting_count: 4 },
          { id: 4, name: 'Michael Torres', role: 'Engineering Manager', department: 'Engineering', avg_sentiment: 0.41, meeting_count: 3 },
          { id: 5, name: 'Elena Volkov', role: 'Junior Developer', department: 'Engineering', avg_sentiment: 0.75, meeting_count: 1 },
          { id: 6, name: 'David Okafor', role: 'Sales Engineer', department: 'Sales', avg_sentiment: 0.45, meeting_count: 2 },
          { id: 7, name: 'Aisha Rahman', role: 'Team Lead', department: 'Mobile', avg_sentiment: 0.82, meeting_count: 3 },
          { id: 8, name: 'Tom Bradley', role: 'Backend Developer', department: 'Engineering', avg_sentiment: 0.18, meeting_count: 2 },
        ]);
      })
      .finally(() => setLoading(false));
  };

  const handleAddEmployee = async (e) => {
    e.preventDefault();
    try {
      await createEmployee(newEmployee);
      setShowAdd(false);
      setNewEmployee({ name: '', role: '', department: '', email: '', manager: '', join_date: '' });
      loadEmployees();
    } catch (err) {
      console.error('Failed to add employee:', err);
    }
  };

  const filtered = employees.filter((emp) =>
    emp.name?.toLowerCase().includes(search.toLowerCase()) ||
    emp.department?.toLowerCase().includes(search.toLowerCase()) ||
    emp.role?.toLowerCase().includes(search.toLowerCase())
  );

  const getSentimentColor = (score) => {
    if (score === null || score === undefined) return 'text-slate-500';
    if (score >= 0.7) return 'text-accent-emerald';
    if (score >= 0.4) return 'text-accent-amber';
    return 'text-accent-rose';
  };

  const getSentimentBg = (score) => {
    if (score === null || score === undefined) return 'bg-slate-500/10';
    if (score >= 0.7) return 'bg-accent-emerald/10';
    if (score >= 0.4) return 'bg-accent-amber/10';
    return 'bg-accent-rose/10';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="w-16 h-16 rounded-full border-4 border-primary-500/30 border-t-primary-500 animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between animate-slide-up">
        <div>
          <h1 className="text-3xl font-bold text-white">
            Employee <span className="gradient-text">Directory</span>
          </h1>
          <p className="text-slate-400 mt-1">{employees.length} team members</p>
        </div>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 text-white rounded-xl font-medium text-sm transition-all shadow-lg shadow-primary-500/20 hover:shadow-primary-500/40"
        >
          <Plus className="w-4 h-4" />
          Add Employee
        </button>
      </div>

      {/* Add Employee Form */}
      {showAdd && (
        <div className="glass-card p-6 animate-slide-up">
          <h3 className="text-white font-semibold mb-4">New Employee</h3>
          <form onSubmit={handleAddEmployee} className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {['name', 'role', 'department', 'email', 'manager'].map((field) => (
              <input
                key={field}
                type={field === 'email' ? 'email' : 'text'}
                placeholder={field.charAt(0).toUpperCase() + field.slice(1)}
                value={newEmployee[field]}
                onChange={(e) => setNewEmployee({ ...newEmployee, [field]: e.target.value })}
                className="bg-surface-900/50 border border-surface-700 rounded-xl px-4 py-2.5 text-white text-sm focus:border-primary-500 focus:outline-none transition-colors"
                required={field === 'name' || field === 'department'}
              />
            ))}
            <input
              type="date"
              value={newEmployee.join_date}
              onChange={(e) => setNewEmployee({ ...newEmployee, join_date: e.target.value })}
              className="bg-surface-900/50 border border-surface-700 rounded-xl px-4 py-2.5 text-white text-sm focus:border-primary-500 focus:outline-none transition-colors"
              required
            />
            <div className="md:col-span-3 flex gap-3">
              <button type="submit" className="px-6 py-2.5 bg-primary-600 hover:bg-primary-500 text-white rounded-xl text-sm font-medium transition-colors">
                Create
              </button>
              <button type="button" onClick={() => setShowAdd(false)} className="px-6 py-2.5 bg-surface-700 hover:bg-surface-600 text-slate-300 rounded-xl text-sm transition-colors">
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-500" />
        <input
          type="text"
          placeholder="Search by name, role, or department..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-surface-800/50 border border-surface-700 rounded-xl pl-12 pr-4 py-3 text-white text-sm focus:border-primary-500 focus:outline-none transition-colors backdrop-blur"
        />
      </div>

      {/* Employee Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((emp, index) => (
          <Link
            key={emp.id}
            to={`/employees/${emp.id}`}
            className="glass-card p-5 group animate-fade-in hover:scale-[1.02] transition-all duration-300"
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500/20 to-accent-cyan/20 flex items-center justify-center border border-primary-500/10">
                  <span className="text-lg font-bold gradient-text">{emp.name?.charAt(0)}</span>
                </div>
                <div>
                  <h3 className="text-white font-semibold group-hover:text-primary-300 transition-colors">{emp.name}</h3>
                  <p className="text-xs text-slate-500">{emp.role}</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-slate-600 group-hover:text-primary-400 transition-colors" />
            </div>
            <div className="mt-4 flex items-center gap-4">
              <span className="text-xs text-slate-400 bg-surface-900/50 px-3 py-1 rounded-full">{emp.department}</span>
              <span className={`text-xs font-medium px-3 py-1 rounded-full ${getSentimentBg(emp.avg_sentiment)} ${getSentimentColor(emp.avg_sentiment)}`}>
                {emp.avg_sentiment !== null && emp.avg_sentiment !== undefined ? `${(emp.avg_sentiment * 100).toFixed(0)}% sentiment` : 'No data'}
              </span>
            </div>
            <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
              <MessageSquare className="w-3.5 h-3.5" />
              {emp.meeting_count || 0} meetings
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default EmployeeList;
