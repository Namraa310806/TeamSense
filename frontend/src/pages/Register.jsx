import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    department: '',
    role: 'EMPLOYEE',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const onChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      const response = await axios.post('/api/auth/register/', form);
      const payload = response.data;
      localStorage.setItem('user', JSON.stringify({
        id: payload.id,
        name: payload.name,
        email: payload.email,
        role: payload.role,
      }));
      localStorage.setItem('access_token', payload.token);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed. Please verify your details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-green-50 p-6">
      <div className="w-full max-w-lg bg-white rounded-2xl shadow-sm border border-green-100 p-8">
        <h1 className="text-2xl font-bold text-slate-800">Create TeamSense Account</h1>
        <p className="text-slate-500 mt-1">Register to access HR analytics dashboards.</p>

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <input
            className="w-full border border-slate-200 rounded-lg px-4 py-3"
            name="name"
            placeholder="Full name"
            value={form.name}
            onChange={onChange}
            required
          />
          <input
            className="w-full border border-slate-200 rounded-lg px-4 py-3"
            type="email"
            name="email"
            placeholder="Email"
            value={form.email}
            onChange={onChange}
            required
          />
          <input
            className="w-full border border-slate-200 rounded-lg px-4 py-3"
            type="password"
            name="password"
            placeholder="Password"
            value={form.password}
            onChange={onChange}
            required
          />
          <input
            className="w-full border border-slate-200 rounded-lg px-4 py-3"
            name="department"
            placeholder="Department"
            value={form.department}
            onChange={onChange}
          />
          <select
            className="w-full border border-slate-200 rounded-lg px-4 py-3"
            name="role"
            value={form.role}
            onChange={onChange}
          >
            <option value="EMPLOYEE">Employee</option>
            <option value="HR">HR</option>
            <option value="ADMIN">Admin</option>
          </select>

          {error && <div className="text-sm text-red-600">{error}</div>}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 text-white rounded-lg py-3 font-semibold disabled:opacity-60"
          >
            {loading ? 'Creating Account...' : 'Register'}
          </button>
        </form>

        <p className="mt-4 text-sm text-slate-600">
          Already have an account? <Link className="text-green-700 font-medium" to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}

export default Register;
