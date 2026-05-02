

const StatChip = ({ label, value, icon: Icon }) => {
  return (
    <div className="glass-card p-4 border border-white/10 rounded-lg">
      <div className="flex items-start justify-between">
        <div>
          <span className="text-xs font-mono uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>{label}</span>
          <div className="text-2xl font-black font-mono mt-2" style={{ color: 'var(--text-primary)' }}>{value}</div>
        </div>
        {Icon && <Icon className="w-5 h-5 mt-1" style={{ color: 'var(--text-muted)' }} />}
      </div>
    </div>
  );
};

export default StatChip;
