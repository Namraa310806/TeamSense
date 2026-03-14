import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Search, Plus, Users, TrendingUp, ChevronRight, MessageSquare, AlertCircle, CheckCircle } from 'lucide-react';
import { fetchEmployees, createEmployee } from '../services/api';

function EmployeeList() {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showAdd, setShowAdd] = useState(false);
  const [newEmployee, setNewEmployee] = useState({ name: '', role: '', department: '', email: '', manager: '', join_date: '' });
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState('');
  const [formSuccess, setFormSuccess] = useState('');

  useEffect(() => {
    loadEmployees();
  }, []);

  const loadEmployees = () => {
    fetchEmployees()
      .then((res) => {
        const data = res.data.results || res.data;
        setEmployees(Array.isArray(data) ? data : []);
      })
      .catch((err) => {
        console.error('Failed to load employees:', err);
        setEmployees([]);
      })
      .finally(() => setLoading(false));
  };

  const handleAddEmployee = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setFormError('');
    setFormSuccess('');

    try {
      const res = await createEmployee(newEmployee);
      const created = res.data;
      setEmployees((prev) => [created, ...prev]);
      setFormSuccess('Employee added successfully!');
      setTimeout(() => {
        setShowAdd(false);
        setFormSuccess('');
        setNewEmployee({ name: '', role: '', department: '', email: '', manager: '', join_date: '' });
      }, 1200);
    } catch (err) {
      const data = err.response?.data;
      if (data) {
        // Format Django validation errors
        const messages = Object.entries(data)
          .map(([key, val]) => `${key}: ${Array.isArray(val) ? val.join(', ') : val}`)
          .join(' | ');
        setFormError(messages || 'Failed to create employee. Please check the fields.');
      } else if (err.response?.status === 401) {
        setFormError('Session expired. Please log out and log in again.');
      } else if (err.response?.status === 403) {
        setFormError('You do not have permission to add employees.');
      } else {
        setFormError('Network error. Check that all containers are running.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const filtered = employees.filter((emp) =>
    emp.name?.toLowerCase().includes(search.toLowerCase()) ||
    emp.department?.toLowerCase().includes(search.toLowerCase()) ||
    emp.role?.toLowerCase().includes(search.toLowerCase())
  );

  const getSentimentColor = (score) => {
    if (score === null || score === undefined) return 'text-slate-400';
    if (score >= 0.7) return 'text-emerald-600';
    if (score >= 0.4) return 'text-amber-600';
    return 'text-rose-600';
  };

  const getSentimentBg = (score) => {
    if (score === null || score === undefined) return 'bg-gray-100';
    if (score >= 0.7) return 'bg-emerald-50';
    if (score >= 0.4) return 'bg-amber-50';
    return 'bg-rose-50';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="w-16 h-16 rounded-full border-4 border-green-200 border-t-green-500 animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between animate-slide-up">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">
            Employee <span className="gradient-text">Directory</span>
          </h1>
          <p className="text-slate-500 mt-1">{employees.length} team members</p>
        </div>
        <button
          onClick={() => { setShowAdd(!showAdd); setFormError(''); setFormSuccess(''); }}
          className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-green-600 to-green-500 hover:from-green-500 hover:to-green-400 text-white rounded-xl font-medium text-sm transition-all shadow-lg shadow-green-500/20 hover:shadow-green-500/40"
        >
          <Plus className="w-4 h-4" />
          Add Employee
        </button>
      </div>

      {/* Add Employee Form */}
      {showAdd && (
        <div className="glass-card p-6 animate-slide-up">
          <h3 className="text-slate-800 font-semibold mb-4">New Employee</h3>

          {/* Error / Success messages */}
          {formError && (
            <div className="flex items-start gap-3 p-3 mb-4 rounded-xl bg-red-50 border border-red-200 text-red-600 text-sm">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{formError}</span>
            </div>
          )}
          {formSuccess && (
            <div className="flex items-center gap-3 p-3 mb-4 rounded-xl bg-green-50 border border-green-200 text-green-700 text-sm">
              <CheckCircle className="w-4 h-4" />
              <span>{formSuccess}</span>
            </div>
          )}

          <form onSubmit={handleAddEmployee} className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { key: 'name', label: 'Full Name', required: true },
              { key: 'role', label: 'Job Title', required: true },
              { key: 'department', label: 'Department', required: true },
              { key: 'email', label: 'Email Address', required: true },
              { key: 'manager', label: 'Manager Name', required: false },
            ].map(({ key, label, required }) => (
              <input
                key={key}
                type={key === 'email' ? 'email' : 'text'}
                placeholder={label}
                value={newEmployee[key]}
                onChange={(e) => setNewEmployee({ ...newEmployee, [key]: e.target.value })}
                className="bg-white border border-gray-200 rounded-xl px-4 py-2.5 text-slate-800 text-sm placeholder-gray-400 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/20 transition-colors"
                required={required}
              />
            ))}
            <input
              type="date"
              value={newEmployee.join_date}
              onChange={(e) => setNewEmployee({ ...newEmployee, join_date: e.target.value })}
              className="bg-white border border-gray-200 rounded-xl px-4 py-2.5 text-slate-800 text-sm focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/20 transition-colors"
              required
            />
            <div className="md:col-span-3 flex gap-3">
              <button
                type="submit"
                disabled={submitting}
                className="px-6 py-2.5 bg-green-600 hover:bg-green-500 text-white rounded-xl text-sm font-medium transition-colors shadow-sm shadow-green-500/20 disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {submitting ? (
                  <><div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Creating...</>
                ) : 'Create Employee'}
              </button>
              <button
                type="button"
                onClick={() => { setShowAdd(false); setFormError(''); }}
                className="px-6 py-2.5 bg-gray-100 hover:bg-gray-200 text-slate-600 rounded-xl text-sm transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search by name, role, or department..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-white border border-gray-200 rounded-xl pl-12 pr-4 py-3 text-slate-800 text-sm placeholder-gray-400 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/20 transition-colors"
        />
      </div>

      {/* Employee Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.length === 0 && !loading && (
          <div className="md:col-span-3 text-center py-16 text-slate-400">
            <Users className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>No employees found. Add your first employee above.</p>
          </div>
        )}
        {filtered.map((emp, index) => (
          <Link
            key={emp.id}
            to={`/employees/${emp.id}`}
            className="glass-card p-5 group animate-fade-in hover:scale-[1.02] transition-all duration-300"
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-100 to-emerald-100 flex items-center justify-center border border-green-200">
                  <span className="text-lg font-bold gradient-text">{emp.name?.charAt(0)}</span>
                </div>
                <div>
                  <h3 className="text-slate-800 font-semibold group-hover:text-green-600 transition-colors">{emp.name}</h3>
                  <p className="text-xs text-slate-500">{emp.role}</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-green-500 transition-colors" />
            </div>
            <div className="mt-4 flex items-center gap-4">
              <span className="text-xs text-slate-500 bg-gray-100 px-3 py-1 rounded-full">{emp.department}</span>
              <span className={`text-xs font-medium px-3 py-1 rounded-full ${getSentimentBg(emp.avg_sentiment)} ${getSentimentColor(emp.avg_sentiment)}`}>
                {emp.avg_sentiment !== null && emp.avg_sentiment !== undefined ? `${(emp.avg_sentiment * 100).toFixed(0)}% sentiment` : 'No data'}
              </span>
            </div>
            <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
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
