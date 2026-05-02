import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import client from '../api/client';
import { 
  ArrowLeft, Mail, Phone, Award, Briefcase, GraduationCap, 
  BarChart3, FileText, Clock, Loader2, CheckCircle, AlertCircle, Zap
} from 'lucide-react';
import { 
  Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer,
  PieChart as RechartsPieChart, Pie, Cell
} from 'recharts';
import GradeBadge from '../components/GradeBadge';
import ScoreBar from '../components/ScoreBar';
import StatChip from '../components/StatChip';
import PublicationCard from '../components/PublicationCard';
import SkeletonLoader from '../components/SkeletonLoader';
import ScoreCard from '../components/ScoreCard';
import BadgeFlag from '../components/BadgeFlag';
import SkillsTab from '../components/SkillsTab';

const CandidateDetailPage = () => {
  const { id } = useParams();
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('education');

  useEffect(() => {
    const fetchCandidate = async () => {
      try {
        const response = await client.get(`/candidates/${id}`);
        setCandidate(response.data);
        setLoading(false);
      } catch (error) {
        console.error('Fetch failed:', error);
        setLoading(false);
      }
    };
    fetchCandidate();
  }, [id]);

  if (loading) return (
    <div className="p-10 space-y-6">
      <SkeletonLoader className="h-10 w-1/4" />
      <div className="grid grid-cols-3 gap-6">
        <SkeletonLoader className="h-96 col-span-1" />
        <SkeletonLoader className="h-96 col-span-2" />
      </div>
    </div>
  );

  if (!candidate) return <div className="p-10 text-center">Candidate not found</div>;

  const summary = candidate.cv_summary;
  const detailedData = summary?.summary_data ? JSON.parse(summary.summary_data) : {};

  // Radar Data
  const radarData = [
    { subject: 'Education', A: summary?.education_score || 0, fullMark: 10 },
    { subject: 'Research', A: summary?.research_score || 0, fullMark: 10 },
    { subject: 'Experience', A: summary?.experience_score || 0, fullMark: 10 },
    { subject: 'TVS', A: summary?.tvs_score || 0, fullMark: 10 },
  ];

  const tabs = [
    { id: 'education', label: 'Education', icon: GraduationCap },
    { id: 'experience', label: 'Experience', icon: Briefcase },
    { id: 'research', label: 'Research', icon: Award },
    { id: 'skills', label: 'Skills', icon: FileText },
    { id: 'tvs_ccs', label: 'TVS/CCS', icon: BarChart3 },
    { id: 'summary', label: 'Summary', icon: FileText },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'education': {
        const eduScores = candidate.education_scores?.[0];
        const eduReasons = eduScores?.reasons ? JSON.parse(eduScores.reasons) : {};
        
        return (
          <div className="space-y-8 animate-in fade-in duration-500">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <h4 className="text-sm font-mono uppercase tracking-widest mb-4" style={{ color: 'var(--text-muted)' }}>Educational History</h4>
                {candidate.education?.length > 0 ? (
                  <div className="space-y-4">
                    {candidate.education.map((edu, idx) => (
                      <div key={idx} className="glass-card p-4">
                        <div className="font-bold" style={{ color: 'var(--text-primary)' }}>{edu.degree}</div>
                        <div className="text-sm text-brand-teal">{edu.institution}</div>
                        <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{edu.year} • GPA: {edu.gpa || 'N/A'}</div>
                      </div>
                    ))}
                  </div>
                ) : <p className="italic" style={{ color: 'var(--text-muted)' }}>No education records found.</p>}
              </div>
              
              <div>
                <h4 className="text-sm font-mono uppercase tracking-widest mb-4" style={{ color: 'var(--text-muted)' }}>Academic Scoring Breakdown</h4>
                {eduScores && (
                  <>
                    <div className="mb-6 p-4 glass-card bg-brand-teal/5 border border-brand-teal/20 rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-bold" style={{ color: 'var(--text-secondary)' }}>Raw Score</span>
                        <div className="flex items-center gap-2">
                          <span className="text-2xl font-black font-mono text-brand-teal">{eduScores.raw_score}</span>
                          <span className="text-sm" style={{ color: 'var(--text-muted)' }}>/100</span>
                          <GradeBadge grade={eduScores.grade} />
                        </div>
                      </div>
                    </div>

                    <ScoreCard label="Degree Level" score={eduScores.degree_level_score} max={25} reason={eduReasons.degree_level_reason} />
                    <ScoreCard label="Overall GPA" score={eduScores.overall_gpa_score} max={30} reason={eduReasons.overall_gpa_reason} />
                    <ScoreCard label="Institution Quality" score={eduScores.institution_quality_score} max={20} reason={eduReasons.institution_quality_reason} />
                    <ScoreCard label="Academic Consistency" score={eduScores.consistency_score} max={10} reason={eduReasons.consistency_reason} />
                    <ScoreCard label="Educational Continuity" score={eduScores.continuity_score} max={10} reason={eduReasons.continuity_reason} />
                    <ScoreCard label="Data Completeness (Bonus)" score={eduScores.data_completeness_bonus} max={5} reason={eduReasons.data_completeness_reason} />
                  </>
                )}
              </div>
            </div>
          </div>
        );
      }

      case 'experience': {
        const expScores = candidate.professional_experience_scores?.[0];
        const expGaps = expScores?.gaps ? JSON.parse(expScores.gaps) : [];
        const expFlags = expScores?.flags ? JSON.parse(expScores.flags) : [];

        return (
          <div className="space-y-8 animate-in fade-in duration-500">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <StatChip label="Avg Tenure" value={`${expScores?.avg_tenure_months || 0}m`} />
              <StatChip label="Total Experience" value={`${expScores?.total_experience_months || 0}m`} />
              <StatChip label="Seniority Trend" value={expScores?.seniority_trend || 'N/A'} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <h4 className="text-sm font-mono uppercase tracking-widest mb-4" style={{ color: 'var(--text-muted)' }}>Work Experience</h4>
                {candidate.experience?.length > 0 ? (
                  <div className="space-y-4">
                    {candidate.experience.map((exp, idx) => (
                      <div key={idx} className="glass-card p-4">
                        <div className="font-bold" style={{ color: 'var(--text-primary)' }}>{exp.role}</div>
                        <div className="text-sm text-brand-teal">{exp.company}</div>
                        <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{exp.start_date} - {exp.end_date || 'Present'}</div>
                      </div>
                    ))}
                  </div>
                ) : <p className="italic" style={{ color: 'var(--text-muted)' }}>No experience records found.</p>}
              </div>

              <div>
                <h4 className="text-sm font-mono uppercase tracking-widest mb-4" style={{ color: 'var(--text-muted)' }}>Professional Scoring</h4>
                {expScores && (
                  <>
                    <div className="mb-6 p-4 glass-card bg-brand-teal/5 border border-brand-teal/20 rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-bold" style={{ color: 'var(--text-secondary)' }}>Raw Score</span>
                        <div className="flex items-center gap-2">
                          <span className="text-2xl font-black font-mono text-brand-teal">{expScores.raw_score}</span>
                          <span className="text-sm" style={{ color: 'var(--text-muted)' }}>/60</span>
                          <GradeBadge grade={expScores.grade} />
                        </div>
                      </div>
                    </div>

                    <ScoreCard label="Gap Detection" score={expScores.gap_detection_score} max={8} />
                    <ScoreCard label="Overlap Analysis" score={expScores.overlap_analysis_score} max={6} />
                    <ScoreCard label="Gap Justification" score={expScores.gap_justification_score} max={6} />
                    <ScoreCard label="Role Seniority" score={expScores.role_seniority_score} max={10} />
                    <ScoreCard label="Tenure Consistency" score={expScores.tenure_consistency_score} max={8} />
                    <ScoreCard label="Domain Continuity" score={expScores.domain_continuity_score} max={7} />
                    <ScoreCard label="Data Quality Bonus" score={expScores.data_quality_bonus} max={15} />

                    {expFlags.length > 0 && (
                      <div className="mt-6 pt-4 border-t border-white/5">
                        <h5 className="text-xs font-bold text-brand-rose uppercase mb-3">🚩 Flags</h5>
                        <div className="space-y-2">
                          {expFlags.map((flag, idx) => (
                            <BadgeFlag key={idx} type="warning" text={flag} />
                          ))}
                        </div>
                      </div>
                    )}

                    {expGaps.length > 0 && (
                      <div className="mt-6 pt-4 border-t border-white/5">
                        <h5 className="text-xs font-bold text-brand-amber uppercase mb-3">Employment Gaps</h5>
                        <div className="space-y-3">
                          {expGaps.map((gap, idx) => (
                            <div key={idx} className="glass-card p-3 bg-amber-500/5 border border-amber-500/20">
                              <div className="flex justify-between items-start mb-1">
                                <span className="text-sm font-mono" style={{ color: 'var(--text-secondary)' }}>{gap.period}</span>
                                <span className="text-xs text-amber-400 font-bold">{gap.months} months</span>
                              </div>
                              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                                {gap.justified ? '✓ Justified' : '✗ Not Justified'}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        );
      }

      case 'research': {
        const resScores = candidate.research_scores?.[0];
        const resWarnings = resScores?.warnings ? JSON.parse(resScores.warnings) : [];
        const resRecommendations = resScores?.recommendations ? JSON.parse(resScores.recommendations) : [];

        return (
          <div className="space-y-8 animate-in fade-in duration-500">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <StatChip label="Publications" value={resScores?.total_journal_papers + resScores?.total_conference_papers || 0} />
              <StatChip label="Journals" value={resScores?.total_journal_papers || 0} />
              <StatChip label="Conference" value={resScores?.total_conference_papers || 0} />
              <StatChip label="Patents" value={resScores?.total_patents || 0} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <h4 className="text-sm font-mono uppercase tracking-widest mb-4" style={{ color: 'var(--text-muted)' }}>Key Publications</h4>
                {candidate.publications?.length > 0 ? (
                  <div className="max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                    {candidate.publications.map((pub, idx) => (
                      <PublicationCard key={idx} pub={pub} />
                    ))}
                  </div>
                ) : <p className="italic" style={{ color: 'var(--text-muted)' }}>No publications found.</p>}
              </div>

              <div>
                <h4 className="text-sm font-mono uppercase tracking-widest mb-4" style={{ color: 'var(--text-muted)' }}>Research Scoring</h4>
                {resScores && (
                  <>
                    <div className="mb-6 p-4 glass-card bg-brand-teal/5 border border-brand-teal/20 rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-bold" style={{ color: 'var(--text-secondary)' }}>Raw Score</span>
                        <div className="flex items-center gap-2">
                          <span className="text-2xl font-black font-mono text-brand-teal">{resScores.raw_score}</span>
                          <span className="text-sm" style={{ color: 'var(--text-muted)' }}>/100</span>
                          <GradeBadge grade={resScores.grade} />
                        </div>
                      </div>
                    </div>

                    <ScoreCard label="Publication Quality" score={resScores.publication_quality_score} max={35} />
                    <ScoreCard label="Authorship Strength" score={resScores.authorship_strength_score} max={20} />
                    <ScoreCard label="Research Collaboration" score={resScores.research_collaboration_score} max={15} />
                    <ScoreCard label="Conference Maturity" score={resScores.conference_maturity_score} max={12} />
                    <ScoreCard label="Patents & Books" score={resScores.patents_books_score} max={10} />
                    <ScoreCard label="Supervision Record" score={resScores.supervision_record_score} max={8} />

                    {resWarnings.length > 0 && (
                      <div className="mt-6 pt-4 border-t border-white/5">
                        <h5 className="text-xs font-bold text-brand-amber uppercase mb-3">⚠️ Warnings</h5>
                        <div className="space-y-2">
                          {resWarnings.map((warning, idx) => (
                            <BadgeFlag key={idx} type="amber" text={warning} />
                          ))}
                        </div>
                      </div>
                    )}

                    {resRecommendations.length > 0 && (
                      <div className="mt-6 pt-4 border-t border-white/5">
                        <h5 className="text-xs font-bold text-brand-teal uppercase mb-3">💡 Recommendations</h5>
                        <ul className="space-y-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                          {resRecommendations.map((rec, idx) => (
                            <li key={idx} className="flex gap-2">
                              <span className="text-brand-teal">→</span> {rec}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        );
      }

      case 'skills': {
        return <SkillsTab candidate={candidate} />;
      }

      case 'tvs_ccs': {
        const tvsScores = candidate.topic_variability_scores?.[0];
        const ccScores = candidate.coauthor_analysis_scores?.[0];
        const topCollabs = ccScores?.top_collaborators ? JSON.parse(ccScores.top_collaborators) : [];

        return (
          <div className="space-y-8 animate-in fade-in duration-500">
            {/* Topic Variability Section */}
            <div className="glass-card p-6">
              <h4 className="text-sm font-mono uppercase tracking-widest mb-6" style={{ color: 'var(--text-muted)' }}>📊 Topic Variability</h4>
              {tvsScores ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="glass-card p-3 bg-white/5">
                      <div className="text-xs uppercase mb-1" style={{ color: 'var(--text-muted)' }}>Dominant Theme</div>
                      <div className="text-sm font-bold text-brand-teal truncate">{tvsScores.dominant_theme}</div>
                    </div>
                    <div className="glass-card p-3 bg-white/5">
                      <div className="text-xs uppercase mb-1" style={{ color: 'var(--text-muted)' }}>Focus Type</div>
                      <div className="text-sm font-bold text-brand-teal">{tvsScores.focus_type}</div>
                    </div>
                    <div className="glass-card p-3 bg-white/5">
                      <div className="text-xs uppercase mb-1" style={{ color: 'var(--text-muted)' }}>Topic Trend</div>
                      <div className="text-sm font-bold text-brand-teal">{tvsScores.topic_trend}</div>
                    </div>
                    <div className="glass-card p-3 bg-white/5">
                      <div className="text-xs uppercase mb-1" style={{ color: 'var(--text-muted)' }}>Themes Identified</div>
                      <div className="text-sm font-bold text-brand-teal">{tvsScores.themes_identified}</div>
                    </div>
                  </div>

                  <ScoreCard label="Research Diversity Score" score={tvsScores.diversity_score} max={10} />
                  
                  <div className="mt-4 p-4 glass-card bg-brand-teal/5 border border-brand-teal/20">
                    <h5 className="text-xs font-bold uppercase mb-2" style={{ color: 'var(--text-muted)' }}>Overall Interpretation</h5>
                    <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{tvsScores.overall_interpretation}</p>
                  </div>
                </div>
              ) : (
                <p className="italic" style={{ color: 'var(--text-muted)' }}>Topic variability data not available.</p>
              )}
            </div>

            {/* Co-Author Analysis Section */}
            <div className="glass-card p-6">
              <h4 className="text-sm font-mono uppercase tracking-widest mb-6" style={{ color: 'var(--text-muted)' }}>🤝 Co-Author Analysis</h4>
              {ccScores ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="glass-card p-3 bg-white/5">
                      <div className="text-xs uppercase mb-1" style={{ color: 'var(--text-muted)' }}>Unique Co-authors</div>
                      <div className="text-lg font-bold text-brand-teal">{ccScores.unique_coauthors}</div>
                    </div>
                    <div className="glass-card p-3 bg-white/5">
                      <div className="text-xs uppercase mb-1" style={{ color: 'var(--text-muted)' }}>Total Collaborations</div>
                      <div className="text-lg font-bold text-brand-teal">{ccScores.total_collaborations}</div>
                    </div>
                    <div className="glass-card p-3 bg-white/5">
                      <div className="text-xs uppercase mb-1" style={{ color: 'var(--text-muted)' }}>Solo Papers</div>
                      <div className="text-lg font-bold text-brand-teal">{ccScores.solo_papers}</div>
                    </div>
                    <div className="glass-card p-3 bg-white/5">
                      <div className="text-xs uppercase mb-1" style={{ color: 'var(--text-muted)' }}>Avg Authors/Paper</div>
                      <div className="text-lg font-bold text-brand-teal">{ccScores.avg_authors_per_paper?.toFixed(1)}</div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="glass-card p-3 bg-white/5">
                      <div className="text-xs uppercase mb-1" style={{ color: 'var(--text-muted)' }}>Collaboration Style</div>
                      <div className="text-sm font-bold text-brand-teal">{ccScores.collaboration_style}</div>
                    </div>
                    <div className="glass-card p-3 bg-white/5">
                      <div className="text-xs uppercase mb-1" style={{ color: 'var(--text-muted)' }}>International</div>
                      <BadgeFlag type={ccScores.international_flag ? 'success' : 'info'} text={ccScores.international_flag ? 'Yes' : 'No'} />
                    </div>
                  </div>

                  <ScoreCard label="Network Diversity Score" score={ccScores.network_diversity_score} max={10} />

                  <div className="mt-4 p-4 glass-card bg-brand-teal/5 border border-brand-teal/20">
                    <h5 className="text-xs font-bold uppercase mb-2" style={{ color: 'var(--text-muted)' }}>Collaboration Interpretation</h5>
                    <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{ccScores.interpretation}</p>
                  </div>

                  {topCollabs.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-white/5">
                      <h5 className="text-xs font-bold uppercase mb-3" style={{ color: 'var(--text-muted)' }}>Top Collaborators</h5>
                      <div className="space-y-2">
                        {topCollabs.slice(0, 5).map((collab, idx) => (
                          <div key={idx} className="glass-card p-3 bg-white/5 flex justify-between items-center">
                            <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>{collab.name}</span>
                            <span className="text-xs font-mono bg-brand-teal/10 text-brand-teal px-2 py-1 rounded">{collab.count} papers</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p className="italic" style={{ color: 'var(--text-muted)' }}>Co-author analysis data not available.</p>
              )}
            </div>
          </div>
        );
      }

      case 'summary': {
        const summary = candidate.cv_summary;
        const summaryData = summary?.summary_data ? (() => {
          try {
            return JSON.parse(summary.summary_data);
          } catch (e) {
            console.error('Failed to parse summary_data:', e);
            return {};
          }
        })() : {};

        const getGradeColor = (grade) => {
          const g = (grade || '').toUpperCase();
          if (g === 'EXCELLENT') return 'bg-green-500/20 text-green-400 border-green-500/30';
          if (g === 'GOOD') return 'bg-teal-500/20 text-teal-400 border-teal-500/30';
          if (g === 'SATISFACTORY') return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
          if (g === 'WEAK') return 'bg-red-500/20 text-red-400 border-red-500/30';
          return 'bg-slate-500/20 text-slate-500 border-slate-500/30';
        };

        const getProgressBarColor = (percentage) => {
          if (percentage >= 75) return 'bg-green-500';
          if (percentage >= 50) return 'bg-amber-500';
          return 'bg-red-500';
        };

        const topStrengths = summaryData.top_strengths || [];
        const topWeaknesses = summaryData.top_weaknesses || [];
        const recommendations = summaryData.recommendations || [];
        const moduleBreakdown = summaryData.module_summary || [];
        const detailedBreakdown = summaryData.detailed_breakdown || [];
        const summaryInterpretation = summaryData.summary_interpretation || '';

        return (
          <div className="space-y-8 animate-in fade-in duration-500">
            {/* A) Overall Assessment Bar */}
            <div className="glass-card p-8 bg-gradient-to-br from-brand-teal/10 to-brand-teal/5 border border-brand-teal/30">
              <h3 className="text-lg font-bold text-brand-teal mb-2">Overall CV Assessment</h3>
              <p className="text-sm mb-8" style={{ color: 'var(--text-secondary)' }}>{summaryInterpretation || 'CV assessment in progress...'}</p>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="glass-card p-4 bg-white/5 text-center">
                  <div className="text-3xl font-black font-mono text-brand-teal">{summary?.overall_score?.toFixed(1) || '--'}</div>
                  <div className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>Overall Score</div>
                </div>
                <div className="glass-card p-4 bg-white/5 text-center">
                  <div className={`inline-block px-3 py-1 rounded-full border text-sm font-bold ${getGradeColor(summary?.overall_grade)}`}>
                    {(summary?.overall_grade || 'N/A').toUpperCase()}
                  </div>
                  <div className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>Overall Grade</div>
                </div>
                <div className="glass-card p-4 bg-white/5 text-center">
                  <div className="text-xl font-bold text-brand-teal">{summary?.overall_status || 'VERIFIED'}</div>
                  <div className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>Status</div>
                </div>
                <div className="glass-card p-4 bg-white/5 text-center">
                  <div className="text-2xl font-bold text-brand-teal">{moduleBreakdown.length}</div>
                  <div className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>Modules</div>
                </div>
              </div>
            </div>

            {/* B) Module Breakdown — Score Progress Bars */}
            {moduleBreakdown.length > 0 && (
              <div className="glass-card p-6">
                <h4 className="text-sm font-mono uppercase tracking-widest mb-6" style={{ color: 'var(--text-muted)' }}>Module Performance Breakdown</h4>
                <div className="space-y-4">
                  {moduleBreakdown.map((module, idx) => {
                    const percentage = (module.score / module.max) * 100;
                    return (
                      <div key={idx} className="glass-card p-4 bg-white/5 hover:bg-white/10 transition-colors">
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <h5 className="font-bold" style={{ color: 'var(--text-primary)' }}>{module.name}</h5>
                            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Weight: {module.weight}%</p>
                          </div>
                          <div className="flex items-center gap-3">
                            <div className={`px-2 py-1 rounded-full border text-xs font-bold ${getGradeColor(module.grade)}`}>
                              {(module.grade || 'N/A').toUpperCase()}
                            </div>
                            <span className="text-lg font-mono font-bold text-brand-teal">{module.score?.toFixed(1) || 0}/{module.max}</span>
                          </div>
                        </div>
                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                          <div 
                            className={`h-full transition-all duration-500 ${getProgressBarColor(percentage)}`}
                            style={{ width: `${Math.min(percentage, 100)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* C) Per-Module Interpretation Cards */}
            {detailedBreakdown.length > 0 && (
              <div className="glass-card p-6">
                <h4 className="text-sm font-mono uppercase tracking-widest mb-6" style={{ color: 'var(--text-muted)' }}>Detailed Module Assessment</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {detailedBreakdown.map((module, idx) => {
                    const strengths = module.strengths || [];
                    const weaknesses = module.weaknesses || [];
                    const moduleRecs = module.recommendations || [];
                    return (
                      <div key={idx} className="glass-card p-6 bg-white/5 border border-white/10">
                        <div className="flex items-center gap-3 mb-4">
                          <h5 className="font-bold" style={{ color: 'var(--text-primary)' }}>{module.name}</h5>
                          <div className={`px-2 py-1 rounded-full border text-xs font-bold ${getGradeColor(module.grade)}`}>
                            {(module.grade || 'N/A').toUpperCase()}
                          </div>
                        </div>

                        {module.interpretation && (
                          <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>{module.interpretation}</p>
                        )}

                        {strengths.length > 0 && (
                          <div className="mb-4">
                            <h6 className="text-xs font-bold text-green-400 uppercase mb-2">Strengths</h6>
                            <ul className="space-y-1">
                              {strengths.map((strength, sidx) => (
                                <li key={sidx} className="flex gap-2 items-start text-xs" style={{ color: 'var(--text-secondary)' }}>
                                  <CheckCircle className="w-3 h-3 text-green-400 mt-0.5 flex-shrink-0" />
                                  <span>{strength}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {weaknesses.length > 0 && (
                          <div className="mb-4">
                            <h6 className="text-xs font-bold text-red-400 uppercase mb-2">Weaknesses</h6>
                            <ul className="space-y-1">
                              {weaknesses.map((weakness, widx) => (
                                <li key={widx} className="flex gap-2 items-start text-xs" style={{ color: 'var(--text-secondary)' }}>
                                  <AlertCircle className="w-3 h-3 text-red-400 mt-0.5 flex-shrink-0" />
                                  <span>{weakness}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {moduleRecs.length > 0 && (
                          <div>
                            <h6 className="text-xs font-bold text-brand-teal uppercase mb-2">Recommendations</h6>
                            <ul className="space-y-1">
                              {moduleRecs.map((rec, ridx) => (
                                <li key={ridx} className="flex gap-2 items-start text-xs" style={{ color: 'var(--text-secondary)' }}>
                                  <span className="text-brand-teal">→</span>
                                  <span>{rec}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* D) Top-Level Strengths & Weaknesses Panel */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {topStrengths.length > 0 && (
                <div className="glass-card p-6 bg-green-500/5 border border-green-500/20">
                  <h4 className="text-sm font-mono text-green-400 uppercase tracking-widest mb-4">Top Strengths</h4>
                  <ul className="space-y-3">
                    {topStrengths.map((strength, idx) => (
                      <li key={idx} className="flex gap-3 items-start text-sm" style={{ color: 'var(--text-secondary)' }}>
                        <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                        <span>{strength}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {topWeaknesses.length > 0 && (
                <div className="glass-card p-6 bg-red-500/5 border border-red-500/20">
                  <h4 className="text-sm font-mono text-red-400 uppercase tracking-widest mb-4">Top Weaknesses</h4>
                  <ul className="space-y-3">
                    {topWeaknesses.map((weakness, idx) => (
                      <li key={idx} className="flex gap-3 items-start text-sm" style={{ color: 'var(--text-secondary)' }}>
                        <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                        <span>{weakness}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* E) Recommendations Panel */}
            {recommendations.length > 0 && (
              <div className="glass-card p-6 bg-blue-500/5 border border-blue-500/20">
                <h4 className="text-sm font-mono text-blue-400 uppercase tracking-widest mb-6">Recommendations</h4>
                <ol className="space-y-3">
                  {recommendations.map((rec, idx) => (
                    <li key={idx} className="flex gap-4 items-start text-sm" style={{ color: 'var(--text-secondary)' }}>
                      <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-400/20 text-blue-400 font-bold text-xs flex-shrink-0">
                        {idx + 1}
                      </span>
                      <span className="pt-0.5">{rec}</span>
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {/* F) Summary Interpretation */}
            {summaryInterpretation && (
              <div className="glass-card p-6 border-l-4 border-brand-teal bg-brand-teal/5">
                <h4 className="text-sm font-mono uppercase tracking-widest mb-4" style={{ color: 'var(--text-muted)' }}>Summary Interpretation</h4>
                <p className="text-sm italic leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{summaryInterpretation}</p>
              </div>
            )}
          </div>
        );
      }

      default:
        return null;
    }
  };

  return (
    <div className="max-w-7xl mx-auto py-10 px-6">
      <Link to="/candidates" className="inline-flex items-center gap-2 mb-8 transition-colors" style={{ color: 'var(--text-muted)' }} onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--accent)'; }} onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-muted)'; }}>
        <ArrowLeft className="w-4 h-4" /> Back to Database
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Panel: Profile */}
        <div className="lg:col-span-4 space-y-6">
          <div className="glass-card p-8 text-center relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-brand-teal/5 rounded-bl-full -mr-10 -mt-10" />
            
            <div className="w-24 h-24 bg-brand-teal/10 border-2 border-brand-teal/20 rounded-2xl flex items-center justify-center text-3xl font-black text-brand-teal mx-auto mb-6 shadow-[0_0_30px_rgba(0,229,204,0.1)]">
              {candidate.name?.charAt(0)}
            </div>
            
            <h1 className="text-3xl mb-1" style={{ color: 'var(--text-primary)' }}>{candidate.name}</h1>
            <div className="flex items-center justify-center gap-2 text-sm mb-6" style={{ color: 'var(--text-muted)' }}>
              <span className="bg-white/5 px-2 py-0.5 rounded font-mono text-[10px]">ID: {candidate.candidate_id || id}</span>
            </div>

            <div className="flex flex-col gap-3 text-left mb-8">
              <div className="flex items-center gap-3 text-sm" style={{ color: 'var(--text-secondary)' }}>
                <Mail className="w-4 h-4" /> {candidate.email}
              </div>
              <div className="flex items-center gap-3 text-sm" style={{ color: 'var(--text-secondary)' }}>
                <Phone className="w-4 h-4" /> {candidate.phone || 'No phone'}
              </div>
            </div>

            <div className="pt-6 border-t border-white/5 flex items-center justify-between">
              <div className="text-left">
                <div className="text-[10px] font-mono uppercase tracking-widest mb-1" style={{ color: 'var(--text-muted)' }}>Overall Status</div>
                <div className="flex items-center gap-2 text-brand-green font-bold text-sm uppercase">
                  <div className="w-2 h-2 rounded-full bg-brand-green animate-pulse" /> {summary?.overall_status || 'VERIFIED'}
                </div>
              </div>
              <GradeBadge grade={summary?.overall_grade} />
            </div>
          </div>

          <div className="glass-card p-6">
            <h3 className="text-sm font-mono uppercase tracking-widest mb-8 text-center" style={{ color: 'var(--text-muted)' }}>Score Vector</h3>
            {!summary ? (
              <div className="text-center py-10">
                <Clock className="w-10 h-10 text-brand-amber mx-auto mb-3 animate-spin-slow" />
                <p className="text-brand-amber font-mono text-xs">SCORING IN PROGRESS...</p>
              </div>
            ) : (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                    <PolarGrid stroke="#ffffff10" />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} />
                    <Radar
                      name="Score"
                      dataKey="A"
                      stroke="#00e5cc"
                      fill="#00e5cc"
                      fillOpacity={0.3}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            )}
            <div className="mt-4 text-center">
              <div className="text-4xl font-black font-mono text-brand-teal">{summary?.overall_score?.toFixed(1) || '--'}</div>
              <div className="text-[10px] font-mono uppercase tracking-tighter" style={{ color: 'var(--text-muted)' }}>Weighted Aggregate</div>
            </div>
          </div>
        </div>

        {/* Right Panel: Tabs & Details */}
        <div className="lg:col-span-8">
          <div className="glass-card min-h-[700px]">
            <div className="flex border-b border-white/5 bg-white/[0.02]">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex-1 flex items-center justify-center gap-2 py-5 text-sm font-bold transition-all
                    ${activeTab === tab.id 
                      ? 'text-brand-teal bg-brand-teal/5 border-b-2 border-brand-teal' 
                      : 'hover:bg-white/5'}`}
                  style={activeTab === tab.id ? {} : { color: 'var(--text-muted)' }}
                  onMouseEnter={(e) => { if (activeTab !== tab.id) e.currentTarget.style.color = 'var(--text-secondary)'; }}
                  onMouseLeave={(e) => { if (activeTab !== tab.id) e.currentTarget.style.color = 'var(--text-muted)'; }}
                >
                  <tab.icon className="w-4 h-4" />
                  <span className="hidden md:inline">{tab.label}</span>
                </button>
              ))}
            </div>
            
            <div className="p-8">
              {!summary ? (
                <div className="flex flex-col items-center justify-center py-40">
                  <Loader2 className="w-12 h-12 text-brand-teal animate-spin mb-4" />
                  <h3 className="text-xl font-syne mb-2" style={{ color: 'var(--text-primary)' }}>Analyzing Profile...</h3>
                  <p className="text-center max-w-xs" style={{ color: 'var(--text-muted)' }}>Our AI engines are extracting and scoring structural data. This usually takes 30-60 seconds.</p>
                </div>
              ) : renderTabContent()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CandidateDetailPage;
