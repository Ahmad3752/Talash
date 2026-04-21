function renderCellValue(row, field) {
  const value = row?.[field.key];

  if (field.render) {
    return field.render(value, row);
  }

  if (value === null || value === undefined || value === '') {
    return '-';
  }

  if (typeof value === 'boolean') {
    return value ? 'true' : 'false';
  }

  return String(value);
}

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
                <td key={field.key}>{renderCellValue(row, field)}</td>
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

  const publicationFields = [
    { key: 'id', label: 'ID' },
    { key: 'pub_type', label: 'Type' },
    { key: 'title', label: 'Title' },
    { key: 'venue', label: 'Venue (Original)' },
    { key: 'issn', label: 'ISSN' },
    { key: 'year', label: 'Year' },
    { key: 'authors', label: 'Authors' },
    { key: 'authorship_role', label: 'Authorship Role' },
    { key: 'wos_indexed', label: 'WoS Indexed' },
    { key: 'scopus_indexed', label: 'Scopus Indexed' },
    { key: 'quartile', label: 'Quartile' },
    { key: 'impact_factor', label: 'Impact Factor' },
    { key: 'core_rank', label: 'CORE Rank' },
    { key: 'indexed_in', label: 'Indexed In' },
    {
      key: 'doi',
      label: 'DOI',
      render: (value) => {
        if (!value) return '-';
        return (
          <a href={`https://doi.org/${value}`} target="_blank" rel="noreferrer" className="doi-link">
            {value}
          </a>
        );
      },
    },
    { key: 'publisher', label: 'Publisher (CrossRef)' },
    { key: 'journal_name', label: 'Journal Name (CrossRef)' },
    { key: 'conference_name', label: 'Conference Name (CrossRef)' },
    { key: 'conference_maturity', label: 'Conference Maturity' },
    { key: 'proceedings_publisher', label: 'Proceedings Publisher' },
    {
      key: 'display_venue',
      label: 'Display Venue (Preferred)',
      render: (_, row) => {
        if (row?.pub_type === 'journal') {
          return row?.journal_name || row?.venue || '-';
        }
        if (row?.pub_type === 'conference') {
          return row?.conference_name || row?.venue || '-';
        }
        return row?.journal_name || row?.conference_name || row?.venue || '-';
      },
    },
  ];

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
          <p><strong>Candidate ID:</strong> {candidate.candidate_id || '-'}</p>
          <p><strong>Name:</strong> {candidate.name || '-'}</p>
          <p><strong>Email:</strong> {candidate.email || '-'}</p>
          <p><strong>Phone:</strong> {candidate.phone || '-'}</p>
        </section>

        <section className="detail-section">
          <h4>Education</h4>
          {renderRows(candidate.education, [
            { key: 'id', label: 'ID' },
            { key: 'degree', label: 'Degree' },
            { key: 'degree_level', label: 'Degree Level' },
            { key: 'field', label: 'Field' },
            { key: 'institution', label: 'Institution' },
            { key: 'board', label: 'Board' },
            { key: 'start_year', label: 'Start Year' },
            { key: 'end_year', label: 'End Year' },
            { key: 'cgpa', label: 'CGPA' },
            { key: 'cgpa_scale', label: 'CGPA Scale' },
            { key: 'percentage', label: 'Percentage' },
            { key: 'normalized_percentage', label: 'Normalized %' },
          ])}
        </section>

        <section className="detail-section">
          <h4>Experience</h4>
          {renderRows(candidate.experience, [
            { key: 'id', label: 'ID' },
            { key: 'company', label: 'Company' },
            { key: 'role', label: 'Role' },
            { key: 'employment_type', label: 'Type' },
            { key: 'start_date', label: 'Start' },
            { key: 'end_date', label: 'End' },
            { key: 'description', label: 'Description' },
          ])}
        </section>

        <section className="detail-section">
          <h4>Publications</h4>
          {renderRows(candidate.publications, publicationFields)}
        </section>

        <section className="detail-section">
          <h4>Skills</h4>
          {renderRows(candidate.skills, [
            { key: 'id', label: 'ID' },
            { key: 'skill_name', label: 'Skill' },
            { key: 'inferred', label: 'Inferred' },
          ])}
        </section>

        <section className="detail-section">
          <h4>Books</h4>
          {renderRows(candidate.books, [
            { key: 'id', label: 'ID' },
            { key: 'title', label: 'Title' },
            { key: 'authors', label: 'Authors' },
            { key: 'isbn', label: 'ISBN' },
            { key: 'publisher', label: 'Publisher' },
            { key: 'year', label: 'Year' },
            { key: 'url', label: 'URL' },
            { key: 'authorship_role', label: 'Authorship Role' },
          ])}
        </section>

        <section className="detail-section">
          <h4>Patents</h4>
          {renderRows(candidate.patents, [
            { key: 'id', label: 'ID' },
            { key: 'patent_number', label: 'Patent #' },
            { key: 'title', label: 'Title' },
            { key: 'year', label: 'Year' },
            { key: 'inventors', label: 'Inventors' },
            { key: 'country', label: 'Country' },
            { key: 'verification_url', label: 'Verification URL' },
          ])}
        </section>

        <section className="detail-section">
          <h4>Supervised Students</h4>
          {renderRows(candidate.supervised_students, [
            { key: 'id', label: 'ID' },
            { key: 'student_name', label: 'Student Name' },
            { key: 'level', label: 'Level' },
            { key: 'role', label: 'Role' },
            { key: 'graduation_year', label: 'Graduation Year' },
          ])}
        </section>
      </div>
    </div>
  );
}

export default CandidateDetail;
