import { useMemo, useState } from 'react';
import {
  AlertCircle,
  CheckCircle,
  Code2,
  FileCheck2,
  GraduationCap,
  Info,
  Layers3,
  ServerCog,
  ShieldCheck,
  Target,
  Wrench,
} from 'lucide-react';
import StatChip from './StatChip';

const MODULE_META = {
  overview: { label: 'Overview', icon: Code2 },
  technical_skill_match: { label: 'Technical', icon: Wrench },
  project_work_evidence: { label: 'Projects', icon: Layers3 },
  professional_experience: { label: 'Experience', icon: FileCheck2 },
  engineering_practices: { label: 'Practices', icon: ShieldCheck },
  role_specific_fit: { label: 'Role Fit', icon: Target },
  education_certifications: { label: 'Education', icon: GraduationCap },
  cv_quality: { label: 'CV Quality', icon: FileCheck2 },
};

const safeJson = (value, fallback = []) => {
  if (!value) return fallback;
  if (Array.isArray(value) || typeof value === 'object') return value;
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
};

const formatScore = (score) => {
  const value = Number(score);
  return Number.isFinite(value) ? value.toFixed(1) : '0.0';
};

const reasonText = (value) => {
  if (!value) return 'No scoring reason recorded.';
  if (Array.isArray(value)) return value.join(' ');
  if (typeof value !== 'object') return String(value);

  return Object.entries(value)
    .map(([key, val]) => {
      const label = key.replaceAll('_', ' ');
      if (typeof val === 'object') return `${label}: ${JSON.stringify(val)}`;
      return `${label}: ${val}`;
    })
    .join(' | ');
};

const getBarColor = (score, max) => {
  const pct = max > 0 ? (score / max) * 100 : 0;
  if (pct >= 70) return 'bg-brand-green';
  if (pct >= 40) return 'bg-brand-amber';
  return 'bg-brand-rose';
};

const InfoTip = ({ text }) => (
  <span className="relative inline-flex group">
    <Info className="w-4 h-4 text-brand-teal cursor-help" />
    <span className="pointer-events-none absolute right-0 top-6 z-30 hidden w-72 rounded-lg border border-brand-teal/30 bg-[#101522] p-3 text-xs leading-relaxed shadow-xl group-hover:block" style={{ color: 'var(--text-secondary)' }}>
      {text}
    </span>
  </span>
);

const PillList = ({ items }) => {
  if (!items?.length) {
    return <p className="text-xs italic" style={{ color: 'var(--text-muted)' }}>No evidence extracted.</p>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item, idx) => (
        <span key={`${item}-${idx}`} className="px-2.5 py-1 rounded-lg border border-brand-teal/20 bg-brand-teal/5 text-xs font-mono text-brand-teal">
          {item}
        </span>
      ))}
    </div>
  );
};

const EvidenceList = ({ title, items, tone }) => {
  const color = tone === 'good' ? 'text-brand-green' : tone === 'warn' ? 'text-brand-amber' : 'text-brand-teal';
  const Icon = tone === 'good' ? CheckCircle : tone === 'warn' ? AlertCircle : Info;

  return (
    <div>
      <div className={`text-xs font-bold uppercase mb-3 ${color}`}>{title}</div>
      {items?.length ? (
        <ul className="space-y-2">
          {items.map((item, idx) => (
            <li key={idx} className="flex items-start gap-2 text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              <Icon className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${color}`} />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-xs italic" style={{ color: 'var(--text-muted)' }}>None recorded.</p>
      )}
    </div>
  );
};

const ReasonBreakdown = ({ reasons }) => {
  const entries = Object.entries(reasons || {});
  if (!entries.length) return null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {entries.map(([key, value]) => (
        <div key={key} className="rounded-lg border border-white/10 bg-white/[0.03] p-3">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <div className="text-[10px] font-mono uppercase tracking-widest truncate" style={{ color: 'var(--text-muted)' }}>
                {key.replaceAll('_', ' ')}
              </div>
              <div className="mt-1 text-sm font-bold" style={{ color: 'var(--text-primary)' }}>
                {typeof value === 'object' ? 'See details' : value}
              </div>
            </div>
            <InfoTip text={reasonText({ [key]: value })} />
          </div>
        </div>
      ))}
    </div>
  );
};

const ModuleScorePanel = ({ module }) => {
  const score = Number(module?.score || 0);
  const max = Number(module?.max || module?.max_score || 1);
  const width = Math.min((score / max) * 100, 100);

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-brand-teal/20 bg-brand-teal/5 p-5">
        <div className="flex items-start justify-between gap-5">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xl font-bold text-brand-teal">{module.name}</h3>
              <InfoTip text={reasonText(module.reasons)} />
            </div>
            <p className="text-sm mt-2" style={{ color: 'var(--text-secondary)' }}>
              Confidence: {module.confidence || 'N/A'} | Weight: {module.weight ?? 0}%
            </p>
          </div>
          <div className="text-right shrink-0">
            <div className="text-4xl font-black font-mono text-brand-teal">{formatScore(score)}</div>
            <div className="text-xs font-mono uppercase" style={{ color: 'var(--text-muted)' }}>
              /{max} | {module.grade || 'N/A'}
            </div>
          </div>
        </div>
        <div className="h-2 bg-white/10 rounded-full overflow-hidden mt-5">
          <div className={`h-full ${getBarColor(score, max)}`} style={{ width: `${width}%` }} />
        </div>
      </div>

      <ReasonBreakdown reasons={module.reasons} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <EvidenceList title="Evidence Used" items={module.evidence_found || []} tone="good" />
        <EvidenceList title="Missing Evidence" items={module.missing_evidence || []} tone="warn" />
      </div>

      <EvidenceList title="Recommendations" items={module.recommendations || []} />
    </div>
  );
};

const ProjectList = ({ projects }) => {
  if (!projects.length) {
    return <p className="text-sm italic" style={{ color: 'var(--text-muted)' }}>No project evidence extracted.</p>;
  }

  return (
    <div className="space-y-4">
      {projects.map((project, idx) => (
        <div key={idx} className="rounded-lg border border-white/10 bg-white/[0.03] p-4">
          <div className="font-bold mb-1" style={{ color: 'var(--text-primary)' }}>{project.name || `Project ${idx + 1}`}</div>
          <p className="text-xs leading-relaxed mb-3" style={{ color: 'var(--text-muted)' }}>{project.description || 'No description available.'}</p>
          <PillList items={project.technologies || []} />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4">
            <StatChip label="Production" value={project.production_evidence ? 'Yes' : 'Missing'} />
            <StatChip label="Impact" value={project.measurable_impact ? 'Found' : 'Missing'} />
            <StatChip label="Ownership" value={project.ownership_signal ? 'Found' : 'Missing'} />
          </div>
        </div>
      ))}
    </div>
  );
};

const DeveloperEvaluationView = ({ developerScores }) => {
  const [activeModule, setActiveModule] = useState('overview');
  const profile = developerScores?.profile;
  const summary = developerScores?.summary;

  const moduleSummary = useMemo(() => safeJson(summary?.module_summary, []), [summary]);
  const topStrengths = useMemo(() => safeJson(summary?.top_strengths, []), [summary]);
  const topWeaknesses = useMemo(() => safeJson(summary?.top_weaknesses, []), [summary]);
  const recommendations = useMemo(() => safeJson(summary?.recommendations, []), [summary]);
  const languages = useMemo(() => safeJson(profile?.programming_languages, []), [profile]);
  const frameworks = useMemo(() => safeJson(profile?.frameworks_libraries, []), [profile]);
  const databases = useMemo(() => safeJson(profile?.databases, []), [profile]);
  const cloudTools = useMemo(() => safeJson(profile?.cloud_devops_tools, []), [profile]);
  const testingTools = useMemo(() => safeJson(profile?.testing_tools, []), [profile]);
  const practices = useMemo(() => safeJson(profile?.architecture_practices, []), [profile]);
  const projects = useMemo(() => safeJson(profile?.projects, []), [profile]);

  if (!summary) {
    return (
      <div className="flex flex-col items-center justify-center py-32 text-center">
        <Code2 className="w-12 h-12 text-brand-amber mb-4" />
        <h3 className="text-xl mb-2" style={{ color: 'var(--text-primary)' }}>No Developer Evaluation Yet</h3>
        <p className="max-w-md text-sm" style={{ color: 'var(--text-muted)' }}>
          Upload this candidate through the Developer track, or run the developer extraction endpoint for this candidate.
        </p>
      </div>
    );
  }

  const activeModuleData = moduleSummary.find((module) => module.key === activeModule);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex flex-wrap gap-2 border-b border-white/5 pb-4">
        <button
          type="button"
          onClick={() => setActiveModule('overview')}
          className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-bold transition-colors ${
            activeModule === 'overview' ? 'bg-brand-teal text-brand-bg' : 'bg-white/[0.03] text-brand-teal hover:bg-brand-teal/10'
          }`}
        >
          <Code2 className="w-4 h-4" />
          Overview
        </button>
        {moduleSummary.map((module) => {
          const meta = MODULE_META[module.key] || { label: module.name, icon: ServerCog };
          const Icon = meta.icon;
          return (
            <button
              key={module.key}
              type="button"
              onClick={() => setActiveModule(module.key)}
              className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-bold transition-colors ${
                activeModule === module.key ? 'bg-brand-teal text-brand-bg' : 'bg-white/[0.03] text-brand-teal hover:bg-brand-teal/10'
              }`}
            >
              <Icon className="w-4 h-4" />
              {meta.label}
            </button>
          );
        })}
      </div>

      {activeModule === 'overview' ? (
        <div className="space-y-6">
          <div className="rounded-lg border border-brand-teal/20 bg-brand-teal/5 p-6">
            <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
              <div>
                <div className="text-xs font-mono uppercase tracking-widest mb-2" style={{ color: 'var(--text-muted)' }}>
                  Developer Evaluation
                </div>
                <h3 className="text-2xl font-bold text-brand-teal">{summary.overall_grade || 'Developer Score'}</h3>
                <p className="text-sm mt-2" style={{ color: 'var(--text-secondary)' }}>
                  {summary.hiring_recommendation || 'Developer scoring completed.'}
                </p>
              </div>
              <div className="text-right">
                <div className="text-5xl font-black font-mono text-brand-teal">{formatScore(summary.overall_score)}</div>
                <div className="text-xs font-mono uppercase" style={{ color: 'var(--text-muted)' }}>
                  /100 | {(profile?.target_role || summary.selected_role || 'developer').replaceAll('_', ' ')}
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatChip label="Role" value={(profile?.target_role || summary.selected_role || 'developer').replaceAll('_', ' ')} />
            <StatChip label="Seniority" value={profile?.seniority_level || 'N/A'} />
            <StatChip label="Confidence" value={summary.confidence || profile?.extraction_confidence || 'N/A'} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="rounded-lg border border-white/10 bg-white/[0.02] p-5">
              <h4 className="text-sm font-mono uppercase tracking-widest mb-4" style={{ color: 'var(--text-muted)' }}>Technical Evidence</h4>
              <div className="space-y-5">
                <div><div className="text-xs font-bold mb-2" style={{ color: 'var(--text-secondary)' }}>Languages</div><PillList items={languages} /></div>
                <div><div className="text-xs font-bold mb-2" style={{ color: 'var(--text-secondary)' }}>Frameworks & Libraries</div><PillList items={frameworks} /></div>
                <div><div className="text-xs font-bold mb-2" style={{ color: 'var(--text-secondary)' }}>Databases</div><PillList items={databases} /></div>
                <div><div className="text-xs font-bold mb-2" style={{ color: 'var(--text-secondary)' }}>Cloud / DevOps / Testing</div><PillList items={[...cloudTools, ...testingTools]} /></div>
                <div><div className="text-xs font-bold mb-2" style={{ color: 'var(--text-secondary)' }}>Engineering Practices</div><PillList items={practices} /></div>
              </div>
            </div>

            <div className="rounded-lg border border-white/10 bg-white/[0.02] p-5">
              <h4 className="text-sm font-mono uppercase tracking-widest mb-4" style={{ color: 'var(--text-muted)' }}>Extracted Projects</h4>
              <ProjectList projects={projects} />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <EvidenceList title="Top Strengths" items={topStrengths} tone="good" />
            <EvidenceList title="Top Weaknesses" items={topWeaknesses} tone="warn" />
            <EvidenceList title="Recommendations" items={recommendations} />
          </div>
        </div>
      ) : (
        <ModuleScorePanel module={activeModuleData} />
      )}
    </div>
  );
};

export default DeveloperEvaluationView;
