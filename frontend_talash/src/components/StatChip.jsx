

const StatChip = ({ label, value, icon: Icon }) => {
  return (
    <div className="stat-chip">
      <div className="flex items-start justify-between">
        <div>
          <span className="stat-label">{label}</span>
          <div className="stat-value">{value}</div>
        </div>
        {Icon && <Icon className="w-5 h-5 text-slate-600 mt-1" />}
      </div>
    </div>
  );
};

export default StatChip;
