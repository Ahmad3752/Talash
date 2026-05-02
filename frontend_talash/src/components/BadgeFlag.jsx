import { AlertCircle, CheckCircle, Info } from 'lucide-react';

export const BadgeFlag = ({ type = 'warning', text, icon: Icon }) => {
  const baseStyles = 'inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold border';
  
  const typeStyles = {
    warning: 'bg-red-500/10 text-red-400 border-red-500/30',
    success: 'bg-green-500/10 text-green-400 border-green-500/30',
    info: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    amber: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
  };

  const DefaultIcon = {
    warning: AlertCircle,
    success: CheckCircle,
    info: Info,
    amber: AlertCircle,
  }[type];

  return (
    <span className={`${baseStyles} ${typeStyles[type]}`}>
      {Icon ? <Icon className="w-3 h-3" /> : <DefaultIcon className="w-3 h-3" />}
      {text}
    </span>
  );
};

export default BadgeFlag;
