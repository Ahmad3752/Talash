
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
            <span className="text-[10px] font-bold font-mono uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
              {pub.pub_type || 'Publication'}
            </span>
            {pub.quartile && (
              <span className="text-[10px] font-bold font-mono px-1.5 py-0.5 rounded border border-brand-green/30 text-brand-green bg-brand-green/5">
                {pub.quartile}
              </span>
            )}
          </div>
          <h4 className="text-sm font-semibold leading-snug" style={{ color: 'var(--text-primary)' }}>
            {pub.title || 'Untitled Publication'}
          </h4>
          <p className="text-xs mt-1 line-clamp-1" style={{ color: 'var(--text-muted)' }}>
            {pub.venue || 'N/A'} • {pub.year || 'N/A'}
          </p>
          <div className="flex flex-wrap gap-2 mt-2">
            {pub.wos_indexed && (
              <span className="text-[10px] font-bold font-mono" style={{ color: 'var(--text-secondary)', backgroundColor: 'var(--bg-border)' }} className="px-1 rounded">WOS</span>
            )}
            {pub.scopus_indexed && (
              <span className="text-[10px] font-bold font-mono" style={{ color: 'var(--text-secondary)', backgroundColor: 'var(--bg-border)' }} className="px-1 rounded">SCOPUS</span>
            )}
          </div>
        </div>
        <button className="p-2 rounded-lg transition-colors" style={{ color: 'var(--text-muted)' }} onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--accent)'; e.currentTarget.style.backgroundColor = 'var(--accent-hover)'; }} onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.backgroundColor = 'transparent'; }}>
          <ExternalLink className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default PublicationCard;
