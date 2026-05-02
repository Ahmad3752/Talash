import { NavLink } from 'react-router-dom';
import { Users, Upload } from 'lucide-react';

const AppSidebar = () => {
  const navItems = [
    { icon: Upload, label: 'Ingest Data', path: '/' },
    { icon: Users, label: 'Candidates', path: '/candidates' },
  ];

  // TODO: Replace with actual auth context when authentication is implemented
  const currentUser = {
    name: 'Admin User',
    role: 'SYSTEM_ADMIN',
  };

  return (
    <aside className="w-64 h-screen border-r border-white/5 bg-[#080d1a] flex flex-col fixed left-0 top-0 z-50">
      <div className="p-6 flex items-center gap-3">
        <div className="w-8 h-8 bg-brand-teal rounded-lg flex items-center justify-center text-brand-bg font-black italic">
          T
        </div>
        <h1 className="text-xl font-syne tracking-tight">TALASH</h1>
      </div>

      <nav className="flex-1 px-4 py-4 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `
              flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300
              ${isActive 
                ? 'bg-brand-teal/10 text-brand-teal border-l-4 border-brand-teal' 
                : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'}
            `}
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-6 border-t border-white/5">
        <div className="flex items-center gap-3 p-3 glass-card bg-brand-teal/5">
          <div className="w-10 h-10 rounded-full bg-slate-800 border border-brand-teal/30" />
          <div className="overflow-hidden">
            <div className="text-sm font-bold truncate">{currentUser.name}</div>
            <div className="text-[10px] text-brand-teal font-mono">{currentUser.role}</div>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default AppSidebar;
