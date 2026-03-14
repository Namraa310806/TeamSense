import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Users, Brain, LogOut, AudioLines, ShieldCheck } from 'lucide-react';

const BASE_NAV_ITEMS = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/employees', icon: Users, label: 'Employees' },
  { to: '/meeting-analysis', icon: AudioLines, label: 'Meeting Intelligence' },
  { to: '/ai-assistant', icon: Brain, label: 'AI Assistant' },
];

const CHR_NAV_ITEMS = [
  { to: '/hr-management', icon: ShieldCheck, label: 'HR Management' },
];

const ROLE_COLORS = {
  ADMIN: 'bg-purple-50 text-purple-600 border-purple-200',
  HR: 'bg-blue-50 text-blue-600 border-blue-200',
  CHR: 'bg-cyan-50 text-cyan-600 border-cyan-200',
  EXECUTIVE: 'bg-amber-50 text-amber-600 border-amber-200',
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
  const roleColor = ROLE_COLORS[user?.role] || 'bg-gray-100 text-gray-600 border-gray-200';

  // Build nav items: base items + CHR-only items when role matches
  const navItems = [
    ...BASE_NAV_ITEMS,
    ...(user?.role === 'CHR' ? CHR_NAV_ITEMS : []),
  ];

  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('access_token');
    navigate('/login');
  };

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-white border-r border-gray-200 flex flex-col z-50">
      {/* Logo */}
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-green-400 flex items-center justify-center shadow-md shadow-green-500/20">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold gradient-text">TeamSense</h1>
            <p className="text-xs text-gray-400">AI HR Intelligence</p>
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
                      ? 'bg-green-50 text-green-700 border border-green-200 shadow-sm'
                      : 'text-slate-500 hover:text-slate-800 hover:bg-green-50'
                  }`
                }
              >
                <item.icon className="w-5 h-5" />
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>

        {/* CHR section divider */}
        {user?.role === 'CHR' && (
          <div className="mt-6 pt-4 border-t border-gray-100">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-widest px-4 mb-2">
              CHR Admin
            </p>
          </div>
        )}
      </nav>

      {/* User info + Logout */}
      <div className="p-4 border-t border-gray-100 space-y-3">
        {user ? (
          <div className="glass-card p-3 flex items-center gap-3">
            {/* Avatar */}
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-green-500 to-green-400 flex items-center justify-center flex-shrink-0 shadow-sm">
              <span className="text-xs font-bold text-white">{initials}</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-800 truncate">{user.name}</p>
              <span className={`inline-block mt-0.5 text-xs font-medium px-2 py-0.5 rounded-full border ${roleColor}`}>
                {user.role}
              </span>
            </div>
          </div>
        ) : (
          <div className="glass-card p-3 text-center">
            <p className="text-xs text-gray-400">Not signed in</p>
          </div>
        )}

        <button
          id="sidebar-logout"
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium text-slate-500 hover:text-red-600 hover:bg-red-50 border border-transparent hover:border-red-100 transition-all"
        >
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>

        <div className="glass-card p-3 text-center">
          <p className="text-xs text-gray-400">Powered by AI</p>
          <div className="flex items-center justify-center gap-1 mt-1">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse-soft" />
            <p className="text-xs text-green-600 font-medium">System Online</p>
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
