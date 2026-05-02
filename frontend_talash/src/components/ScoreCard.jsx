const ScoreCard = ({ label, score, max, reason, icon: Icon }) => {
  const percentage = max > 0 ? (score / max) * 100 : 0;
  
  const getColor = (val) => {
    const pct = max > 0 ? (val / max) * 100 : 0;
    if (pct >= 70) return 'bg-brand-green';
    if (pct >= 40) return 'bg-brand-amber';
    return 'bg-brand-rose';
  };

  return (
    <div className="glass-card p-4 mb-4 hover:bg-white/[0.05] transition-colors">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          {Icon && <Icon className="w-4 h-4 text-brand-teal" />}
          <span className="text-sm font-medium text-slate-300">{label}</span>
        </div>
        <span className="text-sm font-mono font-bold text-brand-teal">{score}/{max}</span>
      </div>
      <div className="h-2 bg-white/10 rounded-full overflow-hidden mb-2">
        <div 
          className={`h-full transition-all duration-500 ease-out ${getColor(score)}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {reason && (
        <p className="text-xs text-slate-500 italic leading-tight">{reason}</p>
      )}
    </div>
  );
};

export default ScoreCard;
