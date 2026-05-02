
import { ExternalLink, Award, BookOpen, FileText } from 'lucide-react';

const PublicationCard = ({ pub }) => {
  const getIcon = (type) => {
    if (type?.toLowerCase().includes('journal')) return <FileText className="w-4 h-4" />;
    if (type?.toLowerCase().includes('book')) return <BookOpen className="w-4 h-4" />;
    return <Award className="w-4 h-4" />;
  };

  return (
    <div className="glass-card p-4 glass-card-hover mb-3">
      <div className="flex justify-between items-start gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1.5 bg-brand-teal/10 text-brand-teal rounded-lg">
              {getIcon(pub.pub_type)}
            </span>
            <span className="text-[10px] font-bold font-mono uppercase tracking-widest text-slate-500">
              {pub.pub_type || 'Publication'}
            </span>
            {pub.quartile && (
              <span className="text-[10px] font-bold font-mono px-1.5 py-0.5 rounded border border-brand-green/30 text-brand-green bg-brand-green/5">
                {pub.quartile}
              </span>
            )}
          </div>
          <h4 className="text-sm font-semibold text-slate-200 leading-snug">
            {pub.title || 'Untitled Publication'}
          </h4>
          <p className="text-xs text-slate-500 mt-1 line-clamp-1">
            {pub.venue || 'N/A'} • {pub.year || 'N/A'}
          </p>
          <div className="flex flex-wrap gap-2 mt-2">
            {pub.wos_indexed && (
              <span className="text-[10px] font-bold font-mono text-slate-400 bg-white/5 px-1 rounded">WOS</span>
            )}
            {pub.scopus_indexed && (
              <span className="text-[10px] font-bold font-mono text-slate-400 bg-white/5 px-1 rounded">SCOPUS</span>
            )}
          </div>
        </div>
        <button className="p-2 text-slate-500 hover:text-brand-teal hover:bg-brand-teal/10 rounded-lg transition-colors">
          <ExternalLink className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default PublicationCard;
