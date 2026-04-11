function CandidateTable({ candidates, onSelectCandidate }) {
  return (
    <div className="table-wrap">
      <table className="candidate-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Email</th>
            <th>Phone</th>
            <th>Education Count</th>
            <th>Experience Count</th>
            <th>Publications Count</th>
          </tr>
        </thead>
        <tbody>
          {candidates.length === 0 && (
            <tr>
              <td colSpan="7" className="empty-row">
                No candidates found.
              </td>
            </tr>
          )}
          {candidates.map((candidate) => (
            <tr
              key={candidate.id}
              className="clickable-row"
              onClick={() => onSelectCandidate(candidate)}
            >
              <td>{candidate.id}</td>
              <td>{candidate.name || '-'}</td>
              <td>{candidate.email || '-'}</td>
              <td>{candidate.phone || '-'}</td>
              <td>{candidate.education_count ?? candidate.education?.length ?? 0}</td>
              <td>{candidate.experience_count ?? candidate.experience?.length ?? 0}</td>
              <td>{candidate.publications_count ?? candidate.publications?.length ?? 0}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default CandidateTable;
