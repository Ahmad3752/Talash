import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import client from '../api/client';
import {
  Trophy,
  GraduationCap,
  Briefcase,
  FlaskConical,
  Star,
  Users,
  TrendingUp,
  BarChart3,
  ChevronDown,
  Medal,
  ArrowUpRight,
  Loader2,
} from 'lucide-react';

/* ─────────────────────────────────────────────
   Helpers
───────────────────────────────────────────── */
const getScore = (candidate, basis) => {
  const s = candidate?.cv_summary;
  if (!s) return null;
  switch (basis) {
    case 'total':       return s.overall_score        ?? null;
    case 'education':   return s.education_score      ?? null;
    case 'experience':  return s.experience_score     ?? null;
    case 'research':    return s.research_score       ?? null;
    default:            return s.overall_score        ?? null;
  }
};

const medal = (rank) => {
  if (rank === 1) return { label: '🥇', color: '#FFD700', bg: 'rgba(255,215,0,0.12)', border: 'rgba(255,215,0,0.35)' };
  if (rank === 2) return { label: '🥈', color: '#C0C0C0', bg: 'rgba(192,192,192,0.12)', border: 'rgba(192,192,192,0.35)' };
  if (rank === 3) return { label: '🥉', color: '#CD7F32', bg: 'rgba(205,127,50,0.12)', border: 'rgba(205,127,50,0.35)' };
  return null;
};

const scoreColor = (score) => {
  if (score === null) return 'var(--text-secondary)';
  if (score >= 90) return '#22c55e';
  if (score >= 75) return '#00e5cc';
  if (score >= 60) return '#f59e0b';
  return '#ef4444';
};

/* ─────────────────────────────────────────────
   Sub-components
───────────────────────────────────────────── */

/** Circular rank badge */
const RankBadge = ({ rank }) => {
  const m = medal(rank);
  return (
    <div
      className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold font-mono"
      style={{
        background: m ? m.bg : 'color-mix(in srgb, var(--accent) 10%, transparent)',
        border: `1.5px solid ${m ? m.border : 'color-mix(in srgb, var(--accent) 25%, transparent)'}`,
        color: m ? m.color : 'var(--accent)',
      }}
    >
      {rank}
    </div>
  );
};

/** Score pill with color */
const ScorePill = ({ score }) => (
  <span
    className="font-mono font-bold text-sm px-3 py-1 rounded-full"
    style={{
      background: score !== null ? `color-mix(in srgb, ${scoreColor(score)} 12%, transparent)` : 'var(--bg-border)',
      color: score !== null ? scoreColor(score) : 'var(--text-secondary)',
      border: `1px solid ${score !== null ? `color-mix(in srgb, ${scoreColor(score)} 30%, transparent)` : 'var(--bg-border)'}`,
    }}
  >
    {score !== null ? score.toFixed(1) : '—'}
  </span>
);

/** Ranking basis selector card */
const BasisCard = ({ icon: Icon, title, active, onClick }) => (
  <button
    onClick={onClick}
    className="flex flex-col gap-1.5 px-5 py-4 rounded-2xl text-left transition-all duration-300 flex-1 min-w-[120px]"
    style={{
      background: active
        ? 'color-mix(in srgb, var(--accent) 12%, var(--bg-surface))'
        : 'var(--bg-surface)',
      border: `1.5px solid ${active ? 'var(--accent)' : 'var(--bg-border)'}`,
      boxShadow: active ? '0 0 20px color-mix(in srgb, var(--accent) 18%, transparent)' : 'none',
      color: active ? 'var(--accent)' : 'var(--text-secondary)',
    }}
  >
    <Icon
      className="w-5 h-5"
      style={{ color: active ? 'var(--accent)' : 'var(--text-secondary)' }}
    />
    <div className="font-semibold text-sm" style={{ color: active ? 'var(--accent)' : 'var(--text-primary)' }}>
      {title}
    </div>
    <div className="text-[11px]" style={{ color: 'var(--text-secondary)' }}>
      Rank by metric
    </div>
  </button>
);

/** Mini bar for distribution chart */
const DistBar = ({ label, count, max }) => {
  const pct = max > 0 ? (count / max) * 100 : 0;
  return (
    <div className="flex items-center gap-3">
      <span
        className="text-xs font-mono w-16 flex-shrink-0 text-right"
        style={{ color: 'var(--text-secondary)' }}
      >
        {label}
      </span>
      <div
        className="flex-1 rounded-full h-2 overflow-hidden"
        style={{ background: 'var(--bg-border)' }}
      >
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{
            width: `${pct}%`,
            background: 'linear-gradient(90deg, var(--accent), color-mix(in srgb, var(--accent) 60%, #7c3aed))',
          }}
        />
      </div>
      <span
        className="text-xs font-bold w-6 text-right"
        style={{ color: 'var(--text-primary)' }}
      >
        {count}
      </span>
    </div>
  );
};

/** Stat summary card */
const StatSummaryCard = ({ label, value, icon: Icon, accent }) => (
  <div
    className="flex items-center gap-4 p-4 rounded-xl"
    style={{
      background: 'color-mix(in srgb, var(--accent) 7%, var(--bg-surface))',
      border: '1px solid var(--bg-border)',
    }}
  >
    <div
      className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
      style={{
        background: 'color-mix(in srgb, var(--accent) 15%, transparent)',
      }}
    >
      <Icon className="w-5 h-5" style={{ color: 'var(--accent)' }} />
    </div>
    <div>
      <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>{label}</div>
      <div className="text-xl font-bold font-mono" style={{ color: 'var(--text-primary)' }}>
        {value ?? '—'}
      </div>
    </div>
  </div>
);

/* ─────────────────────────────────────────────
   Top-N Selector
───────────────────────────────────────────── */
const TOP_N_OPTIONS = [5, 10, 20, 50];

const TopNSelector = ({ value, onChange }) => (
  <div
    className="flex gap-1 p-1 rounded-xl"
    style={{ background: 'var(--bg-surface)', border: '1px solid var(--bg-border)' }}
  >
    {TOP_N_OPTIONS.map((n) => (
      <button
        key={n}
        onClick={() => onChange(n)}
        className="px-4 py-1.5 rounded-lg text-sm font-semibold transition-all duration-200"
        style={{
          background: value === n ? 'var(--accent)' : 'transparent',
          color: value === n ? 'var(--bg-base)' : 'var(--text-secondary)',
        }}
      >
        Top {n}
      </button>
    ))}
  </div>
);

/* ─────────────────────────────────────────────
   Main Page
───────────────────────────────────────────── */
const BASIS_OPTIONS = [
  { key: 'total',      label: 'Total Score',  icon: Trophy },
  { key: 'education',  label: 'Education',    icon: GraduationCap },
  { key: 'experience', label: 'Experience',   icon: Briefcase },
  { key: 'research',   label: 'Research',     icon: FlaskConical },
];

const RankingsPage = () => {
  const navigate = useNavigate();
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [basis, setBasis] = useState('total');
  const [topN, setTopN] = useState(10);

  useEffect(() => {
    const fetchCandidates = async () => {
      try {
        const res = await client.get('/candidates');
        setCandidates(res.data);
      } catch (e) {
        console.error('Failed to fetch candidates:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchCandidates();
  }, []);

  /* Ranked list — only include candidates with a score for the chosen basis */
  const ranked = useMemo(() => {
    const withScore = candidates
      .filter((c) => getScore(c, basis) !== null)
      .map((c) => ({ ...c, _score: getScore(c, basis) }))
      .sort((a, b) => b._score - a._score)
      .slice(0, topN)
      .map((c, i) => ({ ...c, _rank: i + 1 }));
    return withScore;
  }, [candidates, basis, topN]);

  /* Analytics */
  const analytics = useMemo(() => {
    const scores = candidates
      .map((c) => getScore(c, 'total'))
      .filter((s) => s !== null);
    if (!scores.length) return null;
    const highest = Math.max(...scores);
    const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
    const dist = {
      '90+':    scores.filter((s) => s >= 90).length,
      '80–89':  scores.filter((s) => s >= 80 && s < 90).length,
      '70–79':  scores.filter((s) => s >= 70 && s < 80).length,
      'Below 70': scores.filter((s) => s < 70).length,
    };
    const maxDist = Math.max(...Object.values(dist));
    return { highest, avg, total: candidates.length, dist, maxDist };
  }, [candidates]);

  /* ── Skeleton rows ── */
  const SkeletonRow = () => (
    <tr>
      {[...Array(4)].map((_, i) => (
        <td key={i} className="px-6 py-4">
          <div
            className="h-5 rounded-lg animate-pulse"
            style={{
              background: 'var(--bg-border)',
              width: i === 0 ? '2rem' : i === 1 ? '10rem' : i === 2 ? '4rem' : '5rem',
              margin: i === 2 ? '0 auto' : i === 3 ? '0 0 0 auto' : undefined,
            }}
          />
        </td>
      ))}
    </tr>
  );

  return (
    <div className="max-w-7xl mx-auto py-10 px-6">

      {/* ── Page Header ── */}
      <div className="mb-10">
        <h1
          className="text-4xl mb-2 flex items-center gap-3"
          style={{ color: 'var(--text-primary)' }}
        >
          <span
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: 'color-mix(in srgb, var(--accent) 15%, transparent)' }}
          >
            <Trophy className="w-5 h-5" style={{ color: 'var(--accent)' }} />
          </span>
          Candidate Rankings
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Compare and rank candidates across multiple evaluation dimensions
        </p>
      </div>

      {/* ── Ranking Controls ── */}
      <section className="mb-8">
        <div
          className="p-5 rounded-2xl"
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--bg-border)',
          }}
        >
          <div className="flex flex-wrap items-end justify-between gap-4">
            {/* Basis Cards */}
            <div>
              <p className="text-xs font-mono uppercase tracking-widest mb-3" style={{ color: 'var(--text-secondary)' }}>
                Ranking Basis
              </p>
              <div className="flex flex-wrap gap-3">
                {BASIS_OPTIONS.map((opt) => (
                  <BasisCard
                    key={opt.key}
                    icon={opt.icon}
                    title={opt.label}
                    active={basis === opt.key}
                    onClick={() => setBasis(opt.key)}
                  />
                ))}
              </div>
            </div>

            {/* Top-N Selector */}
            <div className="flex flex-col gap-2">
              <p className="text-xs font-mono uppercase tracking-widest" style={{ color: 'var(--text-secondary)' }}>
                Display
              </p>
              <TopNSelector value={topN} onChange={setTopN} />
            </div>
          </div>
        </div>
      </section>

      {/* ── Dashboard Grid ── */}
      <div className="grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-6">

        {/* ── Left: Leaderboard ── */}
        <div
          className="rounded-2xl overflow-hidden"
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--bg-border)',
          }}
        >
          {/* Table header */}
          <div
            className="px-6 py-4 flex items-center gap-2 border-b"
            style={{ borderColor: 'var(--bg-border)' }}
          >
            <Medal className="w-4 h-4" style={{ color: 'var(--accent)' }} />
            <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>
              Leaderboard
            </span>
            <span
              className="ml-auto text-xs font-mono px-2 py-0.5 rounded-full"
              style={{
                background: 'color-mix(in srgb, var(--accent) 10%, transparent)',
                color: 'var(--accent)',
                border: '1px solid color-mix(in srgb, var(--accent) 20%, transparent)',
              }}
            >
              {BASIS_OPTIONS.find((b) => b.key === basis)?.label}
            </span>
          </div>

          <table className="w-full text-left border-collapse">
            <thead>
              <tr
                style={{
                  background: 'color-mix(in srgb, var(--bg-border) 40%, transparent)',
                }}
              >
                {['Rank', 'Candidate', 'Score', 'Badge'].map((col) => (
                  <th
                    key={col}
                    className="px-6 py-3 text-[10px] font-mono uppercase tracking-widest"
                    style={{ color: 'var(--text-secondary)' }}
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array(5).fill(0).map((_, i) => <SkeletonRow key={i} />)
              ) : ranked.length === 0 ? (
                <tr>
                  <td
                    colSpan={4}
                    className="px-6 py-16 text-center"
                    style={{ color: 'var(--text-secondary)' }}
                  >
                    No ranked candidates yet. Upload and process CVs first.
                  </td>
                </tr>
              ) : (
                ranked.map((c) => {
                  const m = medal(c._rank);
                  return (
                    <tr
                      key={c.id}
                      onClick={() => navigate(`/candidates/${c.id}`)}
                      className="cursor-pointer group transition-all duration-200"
                      style={{
                        background: m
                          ? m.bg
                          : 'transparent',
                        borderBottom: '1px solid var(--bg-border)',
                      }}
                      onMouseEnter={(e) => {
                        if (!m) e.currentTarget.style.background = 'color-mix(in srgb, var(--accent) 5%, transparent)';
                      }}
                      onMouseLeave={(e) => {
                        if (!m) e.currentTarget.style.background = 'transparent';
                      }}
                    >
                      {/* Rank */}
                      <td className="px-6 py-4">
                        <RankBadge rank={c._rank} />
                      </td>

                      {/* Candidate */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div
                            className="w-9 h-9 rounded-xl flex items-center justify-center text-sm font-bold uppercase flex-shrink-0"
                            style={{
                              background: m
                                ? `color-mix(in srgb, ${m.color} 20%, transparent)`
                                : 'color-mix(in srgb, var(--accent) 10%, transparent)',
                              color: m ? m.color : 'var(--accent)',
                              border: `1px solid ${m ? m.border : 'color-mix(in srgb, var(--accent) 20%, transparent)'}`,
                            }}
                          >
                            {c.name?.charAt(0) || '?'}
                          </div>
                          <div>
                            <div
                              className="font-semibold text-sm transition-colors"
                              style={{ color: 'var(--text-primary)' }}
                            >
                              {c.name}
                            </div>
                            <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                              {c.email}
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Score */}
                      <td className="px-6 py-4">
                        <ScorePill score={c._score} />
                      </td>

                      {/* Badge / Grade */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          {c.cv_summary?.overall_grade ? (
                            <span
                              className="text-xs font-mono font-bold px-3 py-1 rounded-full"
                              style={{
                                background: 'color-mix(in srgb, var(--accent) 10%, transparent)',
                                color: 'var(--accent)',
                                border: '1px solid color-mix(in srgb, var(--accent) 25%, transparent)',
                              }}
                            >
                              {c.cv_summary.overall_grade}
                            </span>
                          ) : (
                            <span style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>—</span>
                          )}
                          <ArrowUpRight
                            className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity ml-1"
                            style={{ color: 'var(--accent)' }}
                          />
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>

          {/* Footer */}
          {!loading && ranked.length > 0 && (
            <div
              className="px-6 py-3 text-xs flex items-center justify-between"
              style={{
                borderTop: '1px solid var(--bg-border)',
                color: 'var(--text-secondary)',
              }}
            >
              <span>
                Showing {ranked.length} of {candidates.filter((c) => getScore(c, basis) !== null).length} scored candidates
              </span>
              <span className="font-mono">
                Sorted by · {BASIS_OPTIONS.find((b) => b.key === basis)?.label}
              </span>
            </div>
          )}
        </div>

        {/* ── Right: Analytics ── */}
        <div className="flex flex-col gap-4">

          {/* Summary Stats */}
          <div
            className="rounded-2xl p-5"
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--bg-border)',
            }}
          >
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-4 h-4" style={{ color: 'var(--accent)' }} />
              <span className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>
                Summary Stats
              </span>
            </div>
            {loading ? (
              <div className="flex flex-col gap-3">
                {[...Array(3)].map((_, i) => (
                  <div
                    key={i}
                    className="h-16 rounded-xl animate-pulse"
                    style={{ background: 'var(--bg-border)' }}
                  />
                ))}
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                <StatSummaryCard
                  label="Highest Score"
                  value={analytics ? analytics.highest.toFixed(1) : null}
                  icon={Star}
                />
                <StatSummaryCard
                  label="Average Score"
                  value={analytics ? analytics.avg.toFixed(1) : null}
                  icon={TrendingUp}
                />
                <StatSummaryCard
                  label="Total Candidates"
                  value={analytics ? analytics.total : null}
                  icon={Users}
                />
              </div>
            )}
          </div>

          {/* Score Distribution */}
          <div
            className="rounded-2xl p-5 flex-1"
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--bg-border)',
            }}
          >
            <div className="flex items-center gap-2 mb-5">
              <BarChart3 className="w-4 h-4" style={{ color: 'var(--accent)' }} />
              <span className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>
                Score Distribution
              </span>
            </div>

            {loading ? (
              <div className="flex flex-col gap-4">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="h-3 w-14 rounded animate-pulse" style={{ background: 'var(--bg-border)' }} />
                    <div className="h-2 flex-1 rounded-full animate-pulse" style={{ background: 'var(--bg-border)' }} />
                    <div className="h-3 w-4 rounded animate-pulse" style={{ background: 'var(--bg-border)' }} />
                  </div>
                ))}
              </div>
            ) : !analytics ? (
              <p className="text-sm text-center py-6" style={{ color: 'var(--text-secondary)' }}>
                No data yet
              </p>
            ) : (
              <div className="flex flex-col gap-4">
                {Object.entries(analytics.dist).map(([label, count]) => (
                  <DistBar
                    key={label}
                    label={label}
                    count={count}
                    max={analytics.maxDist}
                  />
                ))}
              </div>
            )}

            {/* Legend */}
            {!loading && analytics && (
              <div
                className="mt-5 pt-4 text-xs flex items-center justify-between"
                style={{
                  borderTop: '1px solid var(--bg-border)',
                  color: 'var(--text-secondary)',
                }}
              >
                <span>Based on Total Score</span>
                <span className="font-mono">{analytics.total} candidates</span>
              </div>
            )}
          </div>

          {/* Loading indicator for live data */}
          {loading && (
            <div className="flex items-center gap-2 justify-center py-2">
              <Loader2 className="w-4 h-4 animate-spin" style={{ color: 'var(--accent)' }} />
              <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>Loading data…</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RankingsPage;
