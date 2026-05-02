import { useState, useEffect } from 'react';
import client from '../api/client';
import { Search, Users, Loader2, ArrowUpRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import GradeBadge from '../components/GradeBadge';
import StatChip from '../components/StatChip';
import SkeletonLoader from '../components/SkeletonLoader';

const CandidatesPage = () => {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const navigate = useNavigate();

  const fetchCandidates = async () => {
    try {
      const response = await client.get('/candidates');
      setCandidates(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Fetch failed:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    const fetchData = async () => {
      if (isMounted) {
        await fetchCandidates();
      }
    };
    fetchData();
    return () => { isMounted = false; };
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      // Auto-refresh if any candidate is still processing (no cv_summary yet)
      const isProcessing = candidates.some(c => !c.cv_summary);
      if (isProcessing || candidates.length === 0) {
        fetchCandidates();
      }
    }, 10000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [candidates.length]);

  const filteredCandidates = candidates.filter(c => 
    c.name?.toLowerCase().includes(search.toLowerCase()) || 
    c.email?.toLowerCase().includes(search.toLowerCase())
  );

  const stats = {
    total: candidates.length,
    processing: candidates.filter(c => !c.cv_summary).length
  };

  return (
    <div className="max-w-7xl mx-auto py-10 px-6">
      <div className="flex justify-between items-end mb-10">
        <div>
          <h1 className="text-4xl mb-2">Candidate Database</h1>
          <p className="text-slate-400">Manage and rank your talent pool with AI-driven insights.</p>
        </div>
        <div className="relative w-80">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input 
            type="text" 
            placeholder="Search candidates..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:outline-none focus:border-brand-teal/50 transition-all font-inter"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
        <StatChip label="Total Candidates" value={stats.total} icon={Users} />
        <StatChip label="Processing" value={stats.processing} icon={Loader2} />
      </div>

      <div className="glass-card">
        <table className="w-full text-left border-collapse">
          <thead className="bg-white/5 text-[10px] uppercase font-mono tracking-widest text-slate-500">
            <tr>
              <th className="px-6 py-4 font-bold">Candidate</th>
              <th className="px-6 py-4 font-bold">Status</th>
              <th className="px-6 py-4 font-bold text-right">Score</th>
              <th className="px-6 py-4 font-bold text-center">Grade</th>
              <th className="px-6 py-4"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {loading ? (
              Array(5).fill(0).map((_, i) => (
                <tr key={i}>
                  <td className="px-6 py-4"><SkeletonLoader className="h-10 w-48" /></td>
                  <td className="px-6 py-4"><SkeletonLoader className="h-6 w-24" /></td>
                  <td className="px-6 py-4 text-right"><SkeletonLoader className="h-6 w-12 ml-auto" /></td>
                  <td className="px-6 py-4 text-center"><SkeletonLoader className="h-6 w-12 mx-auto" /></td>
                  <td className="px-6 py-4"></td>
                </tr>
              ))
            ) : filteredCandidates.length === 0 ? (
              <tr>
                <td colSpan="5" className="px-6 py-10 text-center text-slate-500 italic">No candidates found.</td>
              </tr>
            ) : filteredCandidates.map((c) => {
              const hasCV = c.cv_summary !== null;
              const status = hasCV ? (c.cv_summary.overall_status || 'VERIFIED') : 'PROCESSING';
              const statusColor = hasCV ? 'text-brand-green' : 'text-brand-amber';
              const statusIcon = hasCV ? 'pulsing' : 'spinning';
              return (
              <tr 
                key={c.id} 
                onClick={() => navigate(`/candidates/${c.id}`)}
                className="hover:bg-white/5 cursor-pointer transition-colors group"
              >
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-brand-teal/10 flex items-center justify-center text-brand-teal font-bold uppercase">
                      {c.name?.charAt(0)}
                    </div>
                    <div>
                      <div className="font-bold text-slate-200">{c.name}</div>
                      <div className="text-xs text-slate-500">{c.email}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className={`flex items-center gap-2 text-xs font-mono uppercase ${statusColor}`}>
                    <div className={`w-1.5 h-1.5 rounded-full ${statusColor.replace('text-', 'bg-')} ${hasCV ? 'animate-pulse' : 'animate-spin'}`} /> 
                    {status}
                  </div>
                </td>
                <td className="px-6 py-4 text-right font-mono font-bold text-slate-300">
                  {c.cv_summary?.overall_score?.toFixed(1) || '--'}
                </td>
                <td className="px-6 py-4 text-center">
                  <GradeBadge grade={c.cv_summary?.overall_grade} />
                </td>
                <td className="px-6 py-4 text-right">
                  <button className="p-2 text-slate-600 group-hover:text-brand-teal transition-colors">
                    <ArrowUpRight className="w-5 h-5" />
                  </button>
                </td>
              </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default CandidatesPage;
