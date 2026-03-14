import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Users, Brain, LogOut } from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/employees', icon: Users, label: 'Employees' },
  { to: '/ai-assistant', icon: Brain, label: 'AI Assistant' },
];

const ROLE_COLORS = {
  ADMIN: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  HR: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  CHR: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  EXECUTIVE: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
};

function Sidebar() {
  const navigate = useNavigate();

  // Read user from localStorage
  let user = null;
  try {
    const raw = localStorage.getItem('user');
    if (raw) user = JSON.parse(raw);
  } catch {
    // ignore
  }

  const initials = user?.name
    ? user.name.split(' ').map((w) => w[0]).join('').slice(0, 2).toUpperCase()
    : '?';
  const roleColor = ROLE_COLORS[user?.role] || 'bg-slate-700 text-slate-300 border-slate-600';

  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('access_token');
    navigate('/login');
  };

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-surface-800/80 backdrop-blur-xl border-r border-primary-900/30 flex flex-col z-50">
      {/* Logo */}
      <div className="p-6 border-b border-primary-900/20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-cyan flex items-center justify-center">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold gradient-text">TeamSense</h1>
            <p className="text-xs text-slate-500">AI HR Intelligence</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-6 px-3">
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-primary-600/20 text-primary-300 border border-primary-500/20 shadow-lg shadow-primary-500/5'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-surface-700/50'
                  }`
                }
              >
                <item.icon className="w-5 h-5" />
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* User info + Logout */}
      <div className="p-4 border-t border-primary-900/20 space-y-3">
        {user ? (
          <div className="glass-card p-3 flex items-center gap-3">
            {/* Avatar */}
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary-500 to-accent-cyan flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-bold text-white">{initials}</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-white truncate">{user.name}</p>
              <span className={`inline-block mt-0.5 text-xs font-medium px-2 py-0.5 rounded-full border ${roleColor}`}>
                {user.role}
              </span>
            </div>
          </div>
        ) : (
          <div className="glass-card p-3 text-center">
            <p className="text-xs text-slate-500">Not signed in</p>
          </div>
        )}

        <button
          id="sidebar-logout"
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-accent-rose hover:bg-accent-rose/10 border border-transparent hover:border-accent-rose/20 transition-all"
        >
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>

        <div className="glass-card p-3 text-center">
          <p className="text-xs text-slate-500">Powered by AI</p>
          <div className="flex items-center justify-center gap-1 mt-1">
            <div className="w-1.5 h-1.5 rounded-full bg-accent-emerald animate-pulse-soft" />
            <p className="text-xs text-accent-emerald font-medium">System Online</p>
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
