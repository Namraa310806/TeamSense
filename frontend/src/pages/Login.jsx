import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Brain, Mail, Lock, User, AlertCircle, ArrowRight } from 'lucide-react';

const DEMO_AUTH_ONLY = false;
const DEMO_CREDENTIALS = [
  { label: 'HR Demo', name: 'Riya Shah', email: 'riya@hr.ac.in', password: 'Pass@1234' },
  { label: 'Employee Demo', name: 'Aarav Mehta', email: 'aarav@novatech.com', password: 'Pass@1234' },
  { label: 'Admin Demo', name: 'Admin User', email: 'rutvigsolanki8080@gmail.com', password: 'Pass@1234' },
];

function Login() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const applyDemoCredential = (item) => {
    setName(item.name);
    setEmail(item.email);
    setPassword(item.password);
    setError('');
  };

  const buildDemoUser = (inputName, inputEmail) => {
    const emailLower = (inputEmail || '').toLowerCase();
    let role = 'EMPLOYEE';
    if (emailLower.endsWith('@hr.ac.in')) role = 'HR';
    else if (emailLower.endsWith('@teamsense.admin')) role = 'ADMIN';
    return {
      name: inputName || 'Demo User',
      email: inputEmail || 'demo@teamsense.ai',
      role,
    };
  };

  const completeJwtLogin = (payload) => {
    const { name: userName, email: userEmail, role, token } = payload;
    localStorage.setItem('user', JSON.stringify({ name: userName, email: userEmail, role }));
    localStorage.setItem('access_token', token);
    navigate('/');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (DEMO_AUTH_ONLY) {
      const user = buildDemoUser(name, email);
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.setItem('access_token', 'demo-token');
      navigate('/');
      setLoading(false);
      return;
    }

    try {
      const res = await axios.post('/api/auth/login/', { name, email, password });
      completeJwtLogin(res.data);
    } catch (err) {
      const msg = err.response?.data?.error || 'Login failed. Please check your credentials.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleDemoAccess = async () => {
    setError('');
    const demoName = name || 'CHRO User';
    const demoEmail = email || 'chro@novatech.com';
    try {
      setLoading(true);
      const res = await axios.post('/api/auth/login/', {
        name: demoName,
        email: demoEmail,
        password: password || 'Pass@1234',
      });
      completeJwtLogin(res.data);
    } catch (err) {
      const msg = err.response?.data?.error || 'Demo login failed. Please verify backend is running.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const roleBadges = [
    { label: 'HR', domain: '@hr.ac.in', color: 'bg-blue-50 text-blue-600 border-blue-200' },
    { label: 'EMPLOYEE', domain: 'any valid email', color: 'bg-cyan-50 text-cyan-600 border-cyan-200' },
    { label: 'ADMIN', domain: 'whitelisted emails', color: 'bg-purple-50 text-purple-600 border-purple-200' },
  ];

  return (
    <div className="min-h-screen flex bg-white overflow-hidden">
      {/* Left panel – branding */}
      <div className="hidden lg:flex lg:w-1/2 relative flex-col items-center justify-center p-12 overflow-hidden bg-gradient-to-br from-green-50 to-emerald-100">
        {/* Background gradient orbs */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-green-200/40 blur-3xl" />
          <div className="absolute -bottom-32 -right-32 w-96 h-96 rounded-full bg-emerald-200/30 blur-3xl" />
        </div>

        <div className="relative z-10 text-center max-w-md">
          <div className="flex items-center justify-center mb-8">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-green-500 to-green-400 flex items-center justify-center shadow-2xl shadow-green-500/30">
              <Brain className="w-10 h-10 text-white" />
            </div>
          </div>
          <h1 className="text-4xl font-extrabold text-slate-800 mb-4 tracking-tight">
            Team<span className="gradient-text">Sense</span>
          </h1>
          <p className="text-slate-500 text-lg leading-relaxed mb-10">
            AI-powered HR intelligence platform that transforms workforce data into actionable insights.
          </p>

          {/* Role badges */}
          <div className="space-y-3">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-widest mb-4">Access Roles</p>
            {roleBadges.map((r) => (
              <div
                key={r.label}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl border ${r.color} text-sm bg-white/70`}
              >
                <span className="font-bold w-12">{r.label}</span>
                <span className="text-slate-400">→</span>
                <span className="font-mono text-xs">{r.domain}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right panel – form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-white">
        <div className="w-full max-w-md animate-fade-in">
          {/* Mobile logo */}
          <div className="flex items-center gap-3 mb-10 lg:hidden">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-green-400 flex items-center justify-center">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-2xl font-extrabold text-slate-800">Team<span className="gradient-text">Sense</span></h1>
          </div>

          <div className="mb-8">
            <h2 className="text-3xl font-bold text-slate-800">Welcome back</h2>
            <p className="text-slate-500 mt-2">Sign in to access your HR dashboard</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Name */}
            <div className="group">
              <label className="block text-sm font-medium text-slate-600 mb-2">Full Name</label>
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-green-500 transition-colors" />
                <input
                  id="login-name"
                  type="text"
                  placeholder="Enter your name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full pl-11 pr-4 py-3.5 rounded-xl bg-white border border-gray-200 text-slate-800 placeholder-gray-400 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/20 transition-all"
                  required
                />
              </div>
            </div>

            {/* Email */}
            <div className="group">
              <label className="block text-sm font-medium text-slate-600 mb-2">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-green-500 transition-colors" />
                <input
                  id="login-email"
                  type="email"
                  placeholder="you@hr.ac.in"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-11 pr-4 py-3.5 rounded-xl bg-white border border-gray-200 text-slate-800 placeholder-gray-400 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/20 transition-all"
                  required
                />
              </div>
            </div>

            {/* Password */}
            <div className="group">
              <label className="block text-sm font-medium text-slate-600 mb-2">Password</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-green-500 transition-colors" />
                <input
                  id="login-password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-11 pr-4 py-3.5 rounded-xl bg-white border border-gray-200 text-slate-800 placeholder-gray-400 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/20 transition-all"
                  required
                />
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="flex items-start gap-3 p-4 rounded-xl bg-red-50 border border-red-200 text-red-600 text-sm animate-fade-in">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {/* Submit */}
            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-green-600 to-green-500 hover:from-green-500 hover:to-green-400 text-white rounded-xl py-3.5 font-semibold transition-all shadow-lg shadow-green-500/20 hover:shadow-green-500/40 disabled:opacity-60 disabled:cursor-not-allowed group"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Signing in...
                </>
              ) : (
                <>
                  Sign In
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>

            <button
              id="login-demo"
              type="button"
              onClick={handleDemoAccess}
              className="w-full flex items-center justify-center gap-2 border border-primary-500/40 text-primary-200 rounded-xl py-3 font-semibold hover:bg-primary-500/10 transition-all"
            >
              Continue with Demo Login
            </button>

            <div className="rounded-xl border border-gray-200 bg-green-50/60 p-3">
              <p className="text-xs font-semibold text-slate-600 mb-2 uppercase tracking-wide">Demo Credentials</p>
              <div className="space-y-2">
                {DEMO_CREDENTIALS.map((item) => (
                  <button
                    key={item.label}
                    type="button"
                    onClick={() => applyDemoCredential(item)}
                    className="w-full text-left rounded-lg border border-gray-200 bg-white px-3 py-2 hover:border-green-300 hover:bg-green-50 transition-all"
                  >
                    <p className="text-sm font-semibold text-slate-700">{item.label}</p>
                    <p className="text-xs text-slate-500">{item.email} / {item.password}</p>
                  </button>
                ))}
              </div>
            </div>
          </form>

          <p className="mt-8 text-center text-xs text-slate-400">
            © {new Date().getFullYear()} TeamSense. All rights reserved.
          </p>
          <p className="mt-2 text-center text-sm text-slate-500">
            New user? <Link className="text-green-700 font-medium" to="/register">Create an account</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
