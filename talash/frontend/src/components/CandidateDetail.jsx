function renderRows(rows, fields) {
  if (!Array.isArray(rows) || rows.length === 0) {
    return <p className="muted">No data available.</p>;
  }

  return (
    <div className="detail-table-wrap">
      <table className="detail-table">
        <thead>
          <tr>
            {fields.map((field) => (
              <th key={field.key}>{field.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {fields.map((field) => (
                <td key={field.key}>{row?.[field.key] ?? '-'}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CandidateDetail({ candidate, onClose }) {
  if (!candidate) return null;

  return (
    <div className="detail-overlay" onClick={onClose}>
      <div className="detail-panel" onClick={(event) => event.stopPropagation()}>
        <div className="detail-header">
          <h3>Candidate Details</h3>
          <button type="button" className="ghost-btn" onClick={onClose}>
            Close
          </button>
        </div>

        <section className="detail-section">
          <h4>Personal Info</h4>
          <p><strong>ID:</strong> {candidate.id}</p>
          <p><strong>Name:</strong> {candidate.name || '-'}</p>
          <p><strong>Email:</strong> {candidate.email || '-'}</p>
          <p><strong>Phone:</strong> {candidate.phone || '-'}</p>
        </section>

        <section className="detail-section">
          <h4>Education</h4>
          {renderRows(candidate.education, [
            { key: 'degree', label: 'Degree' },
            { key: 'field', label: 'Field' },
            { key: 'institution', label: 'Institution' },
            { key: 'start_year', label: 'Start Year' },
            { key: 'end_year', label: 'End Year' },
          ])}
        </section>

        <section className="detail-section">
          <h4>Experience</h4>
          {renderRows(candidate.experience, [
            { key: 'company', label: 'Company' },
            { key: 'role', label: 'Role' },
            { key: 'employment_type', label: 'Type' },
            { key: 'start_date', label: 'Start' },
            { key: 'end_date', label: 'End' },
          ])}
        </section>

        <section className="detail-section">
          <h4>Publications</h4>
          {renderRows(candidate.publications, [
            { key: 'type', label: 'Type' },
            { key: 'title', label: 'Title' },
            { key: 'venue', label: 'Venue' },
            { key: 'year', label: 'Year' },
          ])}
        </section>

        <section className="detail-section">
          <h4>Skills</h4>
          {Array.isArray(candidate.skills) && candidate.skills.length > 0 ? (
            <ul className="skills-list">
              {candidate.skills.map((skill, index) => (
                <li key={index}>{skill.skill_name ?? skill}</li>
              ))}
            </ul>
          ) : (
            <p className="muted">No skills available.</p>
          )}
        </section>

        <section className="detail-section">
          <h4>Books</h4>
          {renderRows(candidate.books, [
            { key: 'title', label: 'Title' },
            { key: 'publisher', label: 'Publisher' },
            { key: 'year', label: 'Year' },
          ])}
        </section>

        <section className="detail-section">
          <h4>Patents</h4>
          {renderRows(candidate.patents, [
            { key: 'patent_number', label: 'Patent #' },
            { key: 'title', label: 'Title' },
            { key: 'year', label: 'Year' },
          ])}
        </section>
      </div>
    </div>
  );
}

export default CandidateDetail;
