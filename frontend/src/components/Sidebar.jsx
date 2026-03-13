import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Users, MessageSquare, Brain, TrendingUp } from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/employees', icon: Users, label: 'Employees' },
  { to: '/ai-assistant', icon: Brain, label: 'AI Assistant' },
];

function Sidebar() {
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

      {/* Footer */}
      <div className="p-4 border-t border-primary-900/20">
        <div className="glass-card p-3 text-center">
          <p className="text-xs text-slate-500">Powered by AI</p>
          <div className="flex items-center justify-center gap-1 mt-1">
            <div className="w-1.5 h-1.5 rounded-full bg-accent-emerald animate-pulse-soft"></div>
            <p className="text-xs text-accent-emerald font-medium">System Online</p>
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
