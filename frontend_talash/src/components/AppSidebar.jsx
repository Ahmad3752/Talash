import { NavLink } from 'react-router-dom';
import { Users, Upload, Trophy } from 'lucide-react';

const AppSidebar = () => {
  const navItems = [
    { icon: Upload,  label: 'Ingest Data', path: '/' },
    { icon: Users,   label: 'Candidates', path: '/candidates' },
    { icon: Trophy,  label: 'Rankings',   path: '/rankings' },
  ];

  // TODO: Replace with actual auth context when authentication is implemented
  const currentUser = {
    name: 'Admin User',
    role: 'SYSTEM_ADMIN',
  };

  return (
    <aside 
      className="w-64 h-screen flex flex-col fixed left-0 top-0 z-50"
      style={{
        borderRight: '1px solid var(--bg-border)',
        backgroundColor: 'var(--bg-surface)',
      }}
    >
      <div className="p-6 flex items-center gap-3">
        <div 
          className="w-8 h-8 rounded-lg flex items-center justify-center font-black italic"
          style={{
            backgroundColor: 'var(--accent)',
            color: 'var(--bg-base)',
          }}
        >
          T
        </div>
        <h1 className="text-xl font-syne tracking-tight" style={{ color: 'var(--text-primary)' }}>TALASH</h1>
      </div>

      <nav className="flex-1 px-4 py-4 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `
              flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300
              ${isActive 
                ? 'border-l-4' 
                : 'hover:bg-opacity-50'}
            `}
            style={({ isActive }) => ({
              backgroundColor: isActive ? `var(--accent-hover)` : 'transparent',
              color: isActive ? 'var(--accent)' : 'var(--text-secondary)',
              borderColor: isActive ? 'var(--accent)' : 'transparent',
            })}
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div 
        className="p-6 border-t"
        style={{
          borderColor: 'var(--bg-border)',
        }}
      >
        <div 
          className="flex items-center gap-3 p-3 rounded-lg"
          style={{
            backgroundColor: `color-mix(in srgb, var(--accent) 10%, transparent)`,
            border: '1px solid var(--bg-border)',
          }}
        >
          <div 
            className="w-10 h-10 rounded-full border"
            style={{
              backgroundColor: 'var(--bg-border)',
              borderColor: `color-mix(in srgb, var(--accent) 30%, transparent)`,
            }}
          />
          <div className="overflow-hidden">
            <div className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>{currentUser.name}</div>
            <div className="text-[10px] font-mono" style={{ color: 'var(--accent)' }}>{currentUser.role}</div>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default AppSidebar;
