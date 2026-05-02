import { useState } from 'react';
import { Info } from 'lucide-react';
import GradeBadge from './GradeBadge';

const SkillsTab = ({ candidate }) => {
  const [hoveredSegment, setHoveredSegment] = useState(null);
  const [showTooltip, setShowTooltip] = useState(false);
  
  const skillScores = candidate.skill_alignment_scores?.[0];
  const skillDetails = skillScores?.skill_details 
    ? JSON.parse(skillScores.skill_details) 
    : [];
  
  if (!skillScores || !skillScores.applicable) {
    return (
      <div className="space-y-8 animate-in fade-in duration-500">
        <div className="flex items-center justify-center py-16">
          <div className="glass-card p-8 bg-white/5 border border-white/10 rounded-lg max-w-md text-center">
            <p className="text-sm">
              <span className="font-bold text-brand-amber">⚠️ Not Applicable</span>
              <br className="mt-2" />
              <span className="text-xs mt-2 block" style={{ color: 'var(--text-muted)' }}>
                {skillScores?.applicability_reason || 'Skill alignment scoring not applicable for this candidate.'}
              </span>
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Calculate totals
  const totalSkills = 
    (skillScores?.strong_count || 0) +
    (skillScores?.partial_count || 0) +
    (skillScores?.weak_count || 0) +
    (skillScores?.unsupported_count || 0);

  // Get skill status color
  const getSkillColor = (status) => {
    switch (status) {
      case 'strong':
        return 'border-brand-green text-brand-green';
      case 'partial':
        return 'border-brand-amber text-brand-amber';
      case 'weak':
        return 'border-brand-rose text-brand-rose';
      case 'unsupported':
        return 'border-slate-500 text-slate-500';
      default:
        return 'border-brand-teal text-brand-teal';
    }
  };

  // Get skill color for progress bar
  const getSkillBgColor = (status) => {
    switch (status) {
      case 'strong':
        return 'bg-brand-green';
      case 'partial':
        return 'bg-brand-amber';
      case 'weak':
        return 'bg-brand-rose';
      case 'unsupported':
        return 'bg-slate-500';
      default:
        return 'bg-brand-teal';
    }
  };

  // Get status badge color
  const getStatusBgColor = (status) => {
    switch (status) {
      case 'strong':
        return 'bg-brand-green/10 text-brand-green border-brand-green/30';
      case 'partial':
        return 'bg-brand-amber/10 text-brand-amber border-brand-amber/30';
      case 'weak':
        return 'bg-brand-rose/10 text-brand-rose border-brand-rose/30';
      case 'unsupported':
        return 'bg-slate-500/10 text-slate-500 border-slate-500/30';
      default:
        return 'bg-brand-teal/10 text-brand-teal border-brand-teal/30';
    }
  };

  // Calculate score percentage for color coding
  const scorePercentage = (skillScores.raw_score / skillScores.max_score) * 100;
  const getScoreBarColor = () => {
    if (scorePercentage >= 75) return 'bg-brand-green';
    if (scorePercentage >= 50) return 'bg-brand-amber';
    return 'bg-brand-rose';
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* 1. SCORE HEADER */}
      <div className="glass-card p-6 bg-gradient-to-r from-brand-teal/10 to-white/5 border border-brand-teal/20">
        <div className="mb-4">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-mono uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>Skill Assessment</span>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-3xl font-black font-mono text-brand-teal">
                  {skillScores.raw_score}
                  <span className="text-lg ml-1" style={{ color: 'var(--text-muted)' }}>/40</span>
                </div>
              </div>
              <GradeBadge grade={skillScores.grade} />
            </div>
          </div>

          {/* Progress bar */}
          <div className="h-2 bg-white/10 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ease-out ${getScoreBarColor()}`}
              style={{ width: `${scorePercentage}%` }}
            />
          </div>
        </div>
      </div>

      {/* 2. SKILL DISTRIBUTION BAR (only show if there are evaluated skills) */}
      {totalSkills > 0 && (
        <div className="space-y-4">
          <div>
            <div className="h-7 bg-white/5 rounded-lg overflow-hidden flex border border-white/10">
              {skillScores.strong_count > 0 && (
                <div
                  className="bg-brand-green hover:bg-brand-green/80 transition-all cursor-pointer relative group"
                  style={{
                    width: `${(skillScores.strong_count / totalSkills) * 100}%`,
                  }}
                  onMouseEnter={() => setHoveredSegment('strong')}
                  onMouseLeave={() => setHoveredSegment(null)}
                  title={`Strong: ${skillScores.strong_count} (${Math.round((skillScores.strong_count / totalSkills) * 100)}%)`}
                >
                  {hoveredSegment === 'strong' && (
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-black/90 text-white text-xs rounded whitespace-nowrap z-10">
                      Strong: {skillScores.strong_count} ({Math.round((skillScores.strong_count / totalSkills) * 100)}%)
                    </div>
                  )}
                </div>
              )}
              {skillScores.partial_count > 0 && (
                <div
                  className="bg-brand-amber hover:bg-brand-amber/80 transition-all cursor-pointer relative group"
                  style={{
                    width: `${(skillScores.partial_count / totalSkills) * 100}%`,
                  }}
                  onMouseEnter={() => setHoveredSegment('partial')}
                  onMouseLeave={() => setHoveredSegment(null)}
                  title={`Partial: ${skillScores.partial_count} (${Math.round((skillScores.partial_count / totalSkills) * 100)}%)`}
                >
                  {hoveredSegment === 'partial' && (
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-black/90 text-white text-xs rounded whitespace-nowrap z-10">
                      Partial: {skillScores.partial_count} ({Math.round((skillScores.partial_count / totalSkills) * 100)}%)
                    </div>
                  )}
                </div>
              )}
              {skillScores.weak_count > 0 && (
                <div
                  className="bg-brand-rose hover:bg-brand-rose/80 transition-all cursor-pointer relative group"
                  style={{
                    width: `${(skillScores.weak_count / totalSkills) * 100}%`,
                  }}
                  onMouseEnter={() => setHoveredSegment('weak')}
                  onMouseLeave={() => setHoveredSegment(null)}
                  title={`Weak: ${skillScores.weak_count} (${Math.round((skillScores.weak_count / totalSkills) * 100)}%)`}
                >
                  {hoveredSegment === 'weak' && (
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-black/90 text-white text-xs rounded whitespace-nowrap z-10">
                      Weak: {skillScores.weak_count} ({Math.round((skillScores.weak_count / totalSkills) * 100)}%)
                    </div>
                  )}
                </div>
              )}
              {skillScores.unsupported_count > 0 && (
                <div
                  className="bg-slate-500 hover:bg-slate-600 transition-all cursor-pointer relative group"
                  style={{
                    width: `${(skillScores.unsupported_count / totalSkills) * 100}%`,
                  }}
                  onMouseEnter={() => setHoveredSegment('unsupported')}
                  onMouseLeave={() => setHoveredSegment(null)}
                  title={`Unsupported: ${skillScores.unsupported_count} (${Math.round((skillScores.unsupported_count / totalSkills) * 100)}%)`}
                >
                  {hoveredSegment === 'unsupported' && (
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-black/90 text-white text-xs rounded whitespace-nowrap z-10">
                      Unsupported: {skillScores.unsupported_count} ({Math.round((skillScores.unsupported_count / totalSkills) * 100)}%)
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Stat boxes */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="glass-card p-4 border border-white/10 text-center">
              <div className="text-xs font-mono uppercase mb-2" style={{ color: 'var(--text-muted)' }}>Strong</div>
              <div className="text-2xl font-black text-brand-green">{skillScores.strong_count}</div>
            </div>
            <div className="glass-card p-4 border border-white/10 text-center">
              <div className="text-xs font-mono uppercase mb-2" style={{ color: 'var(--text-muted)' }}>Partial</div>
              <div className="text-2xl font-black text-brand-amber">{skillScores.partial_count}</div>
            </div>
            <div className="glass-card p-4 border border-white/10 text-center">
              <div className="text-xs font-mono uppercase mb-2" style={{ color: 'var(--text-muted)' }}>Weak</div>
              <div className="text-2xl font-black text-brand-rose">{skillScores.weak_count}</div>
            </div>
            <div className="glass-card p-4 border border-white/10 text-center">
              <div className="text-xs font-mono uppercase mb-2" style={{ color: 'var(--text-muted)' }}>Unsupported</div>
              <div className="text-2xl font-black text-brand-rose">{skillScores.unsupported_count}</div>
            </div>
          </div>
        </div>
      )}

      {/* 3. SUB-SCORE CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-card p-4 border border-white/10 hover:bg-white/[0.03] transition-colors">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono uppercase" style={{ color: 'var(--text-muted)' }}>Experience Alignment</span>
            <div
              className="relative group cursor-help"
              onMouseEnter={() => setShowTooltip('experience')}
              onMouseLeave={() => setShowTooltip(null)}
            >
              <Info className="w-4 h-4 text-brand-teal/50 hover:text-brand-teal transition-colors" />
              {showTooltip === 'experience' && (
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-black/90 text-white text-xs rounded whitespace-nowrap z-10">
                  How well listed skills match job roles
                </div>
              )}
            </div>
          </div>
          <div className="text-2xl font-black font-mono text-brand-teal mb-2">
            {skillScores.skill_experience_score}
            <span className="text-xs ml-1" style={{ color: 'var(--text-muted)' }}>/18</span>
          </div>
          <div className="h-1 bg-white/10 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${getScoreBarColor()}`}
              style={{
                width: `${(skillScores.skill_experience_score / 18) * 100}%`,
              }}
            />
          </div>
        </div>

        <div className="glass-card p-4 border border-white/10 hover:bg-white/[0.03] transition-colors">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono uppercase" style={{ color: 'var(--text-muted)' }}>Publication Alignment</span>
            <div
              className="relative group cursor-help"
              onMouseEnter={() => setShowTooltip('publication')}
              onMouseLeave={() => setShowTooltip(null)}
            >
              <Info className="w-4 h-4 text-brand-teal/50 hover:text-brand-teal transition-colors" />
              {showTooltip === 'publication' && (
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-black/90 text-white text-xs rounded whitespace-nowrap z-10">
                  Skills appearing in research output
                </div>
              )}
            </div>
          </div>
          <div className="text-2xl font-black font-mono text-brand-teal mb-2">
            {skillScores.skill_publication_score}
            <span className="text-xs ml-1" style={{ color: 'var(--text-muted)' }}>/12</span>
          </div>
          <div className="h-1 bg-white/10 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${getScoreBarColor()}`}
              style={{
                width: `${(skillScores.skill_publication_score / 12) * 100}%`,
              }}
            />
          </div>
        </div>

        <div className="glass-card p-4 border border-white/10 hover:bg-white/[0.03] transition-colors">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono uppercase" style={{ color: 'var(--text-muted)' }}>Consistency</span>
            <div
              className="relative group cursor-help"
              onMouseEnter={() => setShowTooltip('consistency')}
              onMouseLeave={() => setShowTooltip(null)}
            >
              <Info className="w-4 h-4 text-brand-teal/50 hover:text-brand-teal transition-colors" />
              {showTooltip === 'consistency' && (
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-black/90 text-white text-xs rounded whitespace-nowrap z-10">
                  Same skills across experience & publications
                </div>
              )}
            </div>
          </div>
          <div className="text-2xl font-black font-mono text-brand-teal mb-2">
            {skillScores.skill_consistency_score}
            <span className="text-xs ml-1" style={{ color: 'var(--text-muted)' }}>/10</span>
          </div>
          <div className="h-1 bg-white/10 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${getScoreBarColor()}`}
              style={{
                width: `${(skillScores.skill_consistency_score / 10) * 100}%`,
              }}
            />
          </div>
        </div>
      </div>

      {/* 4. SKILLS TAG CLOUD */}
      <div>
        <h4 className="text-xs font-mono uppercase tracking-widest mb-4" style={{ color: 'var(--text-muted)' }}>Skills Listed</h4>
        {candidate.skills && candidate.skills.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {candidate.skills.map((skill, idx) => {
              // Find the skill in skill_details to get its classification
              const skillDetail = skillDetails.find(
                (sd) => sd.skill.toLowerCase() === skill.skill_name.toLowerCase()
              );
              const status = skillDetail?.status || 'unsupported';
              const colorClass = getSkillColor(status);

              return (
                <span
                  key={idx}
                  className={`px-3 py-1.5 rounded-full text-xs font-bold border border-1.5 bg-white/5 transition-all hover:bg-white/10 ${colorClass}`}
                  title={`Status: ${status}`}
                >
                  {skill.skill_name}
                </span>
              );
            })}
          </div>
        ) : (
          <p className="text-xs italic" style={{ color: 'var(--text-muted)' }}>No skills listed in the CV.</p>
        )}
      </div>
    </div>
  );
};

export default SkillsTab;
