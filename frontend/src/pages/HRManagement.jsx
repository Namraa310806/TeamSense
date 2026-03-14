import { useState, useEffect } from 'react';
import { UserPlus, Trash2, Users, Mail, User, AlertCircle, CheckCircle, Loader2, ShieldCheck } from 'lucide-react';
import { fetchHRUsers, addHRUser, deleteHRUser } from '../services/api';

function HRManagement() {
  const [hrUsers, setHrUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [form, setForm] = useState({ name: '', email: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const loadHRUsers = () => {
    setLoading(true);
    fetchHRUsers()
      .then((res) => setHrUsers(res.data))
      .catch((err) => {
        console.error('Failed to load HR users:', err);
        setError('Failed to load HR users. Please try again.');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadHRUsers();
  }, []);

  const handleAddHR = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    setSuccess('');

    // Basic domain validation
    if (!form.email.toLowerCase().endsWith('@hr.ac.in')) {
      setError('HR user email must end with @hr.ac.in');
      setSubmitting(false);
      return;
    }

    try {
      await addHRUser({ name: form.name.trim(), email: form.email.trim().toLowerCase() });
      setSuccess(`${form.name} has been added as an HR user.`);
      setForm({ name: '', email: '' });
      loadHRUsers();
    } catch (err) {
      const msg =
        err.response?.data?.email?.[0] ||
        err.response?.data?.error ||
        err.response?.data?.detail ||
        'Failed to add HR user. The email may already be registered.';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Remove ${name} from the HR users list?`)) return;
    setDeletingId(id);
    setError('');
    setSuccess('');
    try {
      await deleteHRUser(id);
      setSuccess(`${name} has been removed.`);
      setHrUsers((prev) => prev.filter((u) => u.id !== id));
    } catch (err) {
      setError('Failed to delete HR user. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Page Header */}
      <div className="animate-slide-up">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-cyan-600 flex items-center justify-center shadow-md shadow-cyan-500/20">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-slate-800">
            HR <span className="gradient-text">Management</span>
          </h1>
        </div>
        <p className="text-slate-500 mt-1 ml-13 pl-1">
          Register and manage HR users who can access the system.
        </p>
      </div>

      {/* Global Alerts */}
      {error && (
        <div className="flex items-start gap-3 p-4 rounded-xl bg-red-50 border border-red-200 text-red-600 text-sm animate-fade-in">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}
      {success && (
        <div className="flex items-start gap-3 p-4 rounded-xl bg-green-50 border border-green-200 text-green-700 text-sm animate-fade-in">
          <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>{success}</span>
        </div>
      )}

      {/* Add HR User Card */}
      <div className="glass-card p-6 animate-fade-in">
        <h2 className="text-lg font-semibold text-slate-800 mb-5 flex items-center gap-2">
          <UserPlus className="w-5 h-5 text-cyan-500" />
          Add HR User
        </h2>
        <form onSubmit={handleAddHR} className="flex flex-col sm:flex-row gap-4">
          {/* Name field */}
          <div className="group flex-1">
            <label className="block text-xs font-medium text-slate-500 mb-1.5 uppercase tracking-wider">
              Full Name
            </label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-cyan-500 transition-colors" />
              <input
                id="hr-name"
                type="text"
                placeholder="e.g. Rahul Sharma"
                value={form.name}
                onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
                required
                className="w-full pl-10 pr-4 py-3 rounded-xl bg-white border border-gray-200 text-slate-800 placeholder-gray-400 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/20 transition-all text-sm"
              />
            </div>
          </div>

          {/* Email field */}
          <div className="group flex-1">
            <label className="block text-xs font-medium text-slate-500 mb-1.5 uppercase tracking-wider">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-cyan-500 transition-colors" />
              <input
                id="hr-email"
                type="email"
                placeholder="user@hr.ac.in"
                value={form.email}
                onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))}
                required
                className="w-full pl-10 pr-4 py-3 rounded-xl bg-white border border-gray-200 text-slate-800 placeholder-gray-400 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/20 transition-all text-sm"
              />
            </div>
          </div>

          {/* Submit button */}
          <div className="flex items-end">
            <button
              id="hr-add-btn"
              type="submit"
              disabled={submitting}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-400 hover:to-cyan-500 text-white font-semibold text-sm shadow-md shadow-cyan-500/20 hover:shadow-cyan-500/40 transition-all disabled:opacity-60 disabled:cursor-not-allowed whitespace-nowrap"
            >
              {submitting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <UserPlus className="w-4 h-4" />
              )}
              {submitting ? 'Adding…' : 'Add HR'}
            </button>
          </div>
        </form>
      </div>

      {/* HR Users Table */}
      <div className="glass-card p-6 animate-fade-in">
        <h2 className="text-lg font-semibold text-slate-800 mb-5 flex items-center gap-2">
          <Users className="w-5 h-5 text-cyan-500" />
          Registered HR Users
          {!loading && (
            <span className="ml-auto text-xs font-medium px-2.5 py-1 rounded-full bg-cyan-50 text-cyan-600 border border-cyan-100">
              {hrUsers.length} {hrUsers.length === 1 ? 'user' : 'users'}
            </span>
          )}
        </h2>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="text-center">
              <div className="w-12 h-12 rounded-full border-4 border-cyan-100 border-t-cyan-500 animate-spin mx-auto" />
              <p className="text-slate-500 text-sm mt-3">Loading HR users…</p>
            </div>
          </div>
        ) : hrUsers.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-16 h-16 rounded-full bg-cyan-50 flex items-center justify-center mb-3">
              <Users className="w-8 h-8 text-cyan-300" />
            </div>
            <p className="text-slate-500 font-medium">No HR users yet</p>
            <p className="text-slate-400 text-sm mt-1">Add your first HR user using the form above.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 uppercase tracking-wider">Name</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 uppercase tracking-wider">Email</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 uppercase tracking-wider">Role</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 uppercase tracking-wider">Added</th>
                  <th className="text-right py-3 px-4 text-xs font-medium text-slate-500 uppercase tracking-wider">Action</th>
                </tr>
              </thead>
              <tbody>
                {hrUsers.map((user) => (
                  <tr key={user.id} className="border-b border-gray-100 hover:bg-cyan-50/40 transition-colors group">
                    {/* Name + avatar */}
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-400 to-cyan-500 flex items-center justify-center flex-shrink-0">
                          <span className="text-xs font-bold text-white">
                            {user.name.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <span className="text-slate-800 font-medium text-sm">{user.name}</span>
                      </div>
                    </td>
                    {/* Email */}
                    <td className="py-3.5 px-4">
                      <span className="text-slate-600 text-sm font-mono">{user.email}</span>
                    </td>
                    {/* Role */}
                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-600 border border-blue-100">
                        {user.role}
                      </span>
                    </td>
                    {/* Created at */}
                    <td className="py-3.5 px-4 text-slate-500 text-sm">
                      {new Date(user.created_at).toLocaleDateString('en-IN', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric',
                      })}
                    </td>
                    {/* Delete */}
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => handleDelete(user.id, user.name)}
                        disabled={deletingId === user.id}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-red-500 bg-red-50 hover:bg-red-100 border border-red-100 hover:border-red-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {deletingId === user.id ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <Trash2 className="w-3 h-3" />
                        )}
                        {deletingId === user.id ? 'Removing…' : 'Delete'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default HRManagement;
