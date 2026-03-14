import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Brain, Mail, Lock, User, AlertCircle, ArrowRight } from 'lucide-react';

function Login() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await axios.post('/api/accounts/login/', { name, email, password });
      const { name: userName, email: userEmail, role, token } = res.data;

      // Persist user info to localStorage
      localStorage.setItem('user', JSON.stringify({ name: userName, email: userEmail, role }));
      localStorage.setItem('access_token', token);

      navigate('/');
    } catch (err) {
      const msg = err.response?.data?.error || 'Login failed. Please check your credentials.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const roleBadges = [
    { label: 'HR', domain: '@hr.ac.in', color: 'bg-blue-500/20 text-blue-300 border-blue-500/30' },
    { label: 'CHR', domain: '@chr.ac.in', color: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30' },
    { label: 'ADMIN', domain: 'whitelisted emails', color: 'bg-purple-500/20 text-purple-300 border-purple-500/30' },
  ];

  return (
    <div className="min-h-screen flex bg-surface-900 overflow-hidden">
      {/* Left panel – branding */}
      <div className="hidden lg:flex lg:w-1/2 relative flex-col items-center justify-center p-12 overflow-hidden">
        {/* Background gradient orbs */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-primary-600/20 blur-3xl" />
          <div className="absolute -bottom-32 -right-32 w-96 h-96 rounded-full bg-accent-cyan/10 blur-3xl" />
        </div>

        <div className="relative z-10 text-center max-w-md">
          <div className="flex items-center justify-center mb-8">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500 to-accent-cyan flex items-center justify-center shadow-2xl shadow-primary-500/30">
              <Brain className="w-10 h-10 text-white" />
            </div>
          </div>
          <h1 className="text-4xl font-extrabold text-white mb-4 tracking-tight">
            Team<span className="gradient-text">Sense</span>
          </h1>
          <p className="text-slate-400 text-lg leading-relaxed mb-10">
            AI-powered HR intelligence platform that transforms workforce data into actionable insights.
          </p>

          {/* Role badges */}
          <div className="space-y-3">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-widest mb-4">Access Roles</p>
            {roleBadges.map((r) => (
              <div
                key={r.label}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl border ${r.color} text-sm`}
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
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md animate-fade-in">
          {/* Mobile logo */}
          <div className="flex items-center gap-3 mb-10 lg:hidden">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-cyan flex items-center justify-center">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-2xl font-extrabold text-white">Team<span className="gradient-text">Sense</span></h1>
          </div>

          <div className="mb-8">
            <h2 className="text-3xl font-bold text-white">Welcome back</h2>
            <p className="text-slate-400 mt-2">Sign in to access your HR dashboard</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Name */}
            <div className="group">
              <label className="block text-sm font-medium text-slate-400 mb-2">Full Name</label>
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-primary-400 transition-colors" />
                <input
                  id="login-name"
                  type="text"
                  placeholder="Enter your name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full pl-11 pr-4 py-3.5 rounded-xl bg-surface-800 border border-surface-700 text-white placeholder-slate-600 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
                  required
                />
              </div>
            </div>

            {/* Email */}
            <div className="group">
              <label className="block text-sm font-medium text-slate-400 mb-2">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-primary-400 transition-colors" />
                <input
                  id="login-email"
                  type="email"
                  placeholder="you@hr.ac.in"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-11 pr-4 py-3.5 rounded-xl bg-surface-800 border border-surface-700 text-white placeholder-slate-600 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
                  required
                />
              </div>
            </div>

            {/* Password */}
            <div className="group">
              <label className="block text-sm font-medium text-slate-400 mb-2">Password</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-primary-400 transition-colors" />
                <input
                  id="login-password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-11 pr-4 py-3.5 rounded-xl bg-surface-800 border border-surface-700 text-white placeholder-slate-600 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
                  required
                />
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="flex items-start gap-3 p-4 rounded-xl bg-accent-rose/10 border border-accent-rose/20 text-accent-rose text-sm animate-fade-in">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {/* Submit */}
            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 text-white rounded-xl py-3.5 font-semibold transition-all shadow-lg shadow-primary-500/20 hover:shadow-primary-500/40 disabled:opacity-60 disabled:cursor-not-allowed group"
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
          </form>

          <p className="mt-8 text-center text-xs text-slate-600">
            © {new Date().getFullYear()} TeamSense. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
