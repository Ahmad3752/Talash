import { FileUp, Users } from 'lucide-react';

function Sidebar({ activePage, onChangePage }) {
  return (
    <aside className="sidebar">
      <h1 className="sidebar-title">TALASH</h1>
      <nav className="sidebar-nav">
        <button
          className={`sidebar-item ${activePage === 'upload' ? 'active' : ''}`}
          onClick={() => onChangePage('upload')}
          type="button"
        >
          <FileUp size={18} />
          <span>Upload CV</span>
        </button>
        <button
          className={`sidebar-item ${activePage === 'candidates' ? 'active' : ''}`}
          onClick={() => onChangePage('candidates')}
          type="button"
        >
          <Users size={18} />
          <span>View Candidates</span>
        </button>
      </nav>
    </aside>
  );
}

export default Sidebar;
