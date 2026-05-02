import { useEffect, useState } from 'react';

const ScoreBar = ({ label, score, max = 10, reason }) => {
  const [width, setWidth] = useState(0);
  const percentage = (score / max) * 100;
  
  useEffect(() => {
    const timer = setTimeout(() => setWidth(percentage), 100);
    return () => clearTimeout(timer);
  }, [percentage]);

  const getColor = (val) => {
    if (val >= 7) return 'bg-brand-green';
    if (val >= 4) return 'bg-brand-amber';
    return 'bg-brand-rose';
  };

  return (
    <div className="mb-4">
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>{label}</span>
        <span className="text-sm font-mono font-bold text-brand-teal">{score}/{max}</span>
      </div>
      <div className="h-2 bg-white/10 rounded-full overflow-hidden">
        <div 
          className={`h-full transition-all duration-1000 ease-out ${getColor(score)}`}
          style={{ width: `${width}%` }}
        />
      </div>
      {reason && (
        <p className="mt-1 text-xs italic leading-tight" style={{ color: 'var(--text-muted)' }}>{reason}</p>
      )}
    </div>
  );
};

export default ScoreBar;
