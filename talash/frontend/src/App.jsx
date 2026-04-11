import { useState } from 'react';
import Sidebar from './components/Sidebar';
import CandidatesPage from './pages/CandidatesPage';
import UploadPage from './pages/UploadPage';
import './App.css';

function App() {
  const [activePage, setActivePage] = useState('upload');

  return (
    <div className="app-layout">
      <Sidebar activePage={activePage} onChangePage={setActivePage} />
      <main className="main-content">
        {activePage === 'upload' ? <UploadPage /> : <CandidatesPage />}
      </main>
    </div>
  );
}

export default App;
