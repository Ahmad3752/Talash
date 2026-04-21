import { useEffect, useMemo, useState } from 'react';
import client from '../api/client';
import CandidateDetail from '../components/CandidateDetail';
import CandidateTable from '../components/CandidateTable';

function CandidatesPage() {
  const [candidates, setCandidates] = useState([]);
  const [searchText, setSearchText] = useState('');
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [isLoadingCandidate, setIsLoadingCandidate] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const loadCandidates = async () => {
    setIsLoading(true);
    setError('');
    try {
      const response = await client.get('/api/cv/candidates');
      setCandidates(Array.isArray(response.data) ? response.data : []);
    } catch {
      setError('Could not load candidates. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCandidates();
  }, []);

  const openCandidateDetail = async (candidateSummary) => {
    if (!candidateSummary?.candidate_id) {
      return;
    }

    setIsLoadingCandidate(true);
    setError('');
    try {
      const response = await client.get(`/api/cv/candidates/${candidateSummary.candidate_id}`);
      setSelectedCandidate(response.data || null);
    } catch {
      setError('Could not load candidate details. Please try again.');
    } finally {
      setIsLoadingCandidate(false);
    }
  };

  const filteredCandidates = useMemo(() => {
    return candidates.filter((candidate) =>
      (candidate.name || '').toLowerCase().includes(searchText.toLowerCase())
    );
  }, [candidates, searchText]);

  return (
    <section className="panel">
      <div className="toolbar">
        <h2>Candidates</h2>
        <button type="button" className="primary-btn" onClick={loadCandidates} disabled={isLoading}>
          {isLoading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      <input
        className="search-input"
        type="text"
        placeholder="Search by name..."
        value={searchText}
        onChange={(event) => setSearchText(event.target.value)}
      />

      {error && <div className="card error-card">{error}</div>}

      {isLoading ? <div className="loader-text">Loading candidates...</div> : null}
      {isLoadingCandidate ? <div className="loader-text">Loading full candidate profile...</div> : null}

      <CandidateTable candidates={filteredCandidates} onSelectCandidate={openCandidateDetail} />

      <CandidateDetail candidate={selectedCandidate} onClose={() => setSelectedCandidate(null)} />
    </section>
  );
}

export default CandidatesPage;
