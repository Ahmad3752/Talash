import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import AppSidebar from './components/AppSidebar';
import { ThemeToggle } from './components/ThemeToggle';
import UploadPage from './pages/UploadPage';
import CandidatesPage from './pages/CandidatesPage';
import CandidateDetailPage from './pages/CandidateDetailPage';
import RankingsPage from './pages/RankingsPage';

function App() {
  return (
    <Router>
      <div className="flex min-h-screen" style={{ backgroundColor: 'var(--bg-base)' }}>
        <AppSidebar />
        <main className="flex-1 ml-64 min-h-screen">
          {/* Header with Theme Toggle */}
          <div 
            className="sticky top-0 right-0 p-4 flex justify-end border-b z-40"
            style={{
              borderColor: 'var(--bg-border)',
              backgroundColor: 'var(--bg-base)',
            }}
          >
            <ThemeToggle />
          </div>
          
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/candidates" element={<CandidatesPage />} />
            <Route path="/candidates/:id" element={<CandidateDetailPage />} />
            <Route path="/rankings" element={<RankingsPage />} />
            <Route path="*" element={<div className="p-20 text-center">Page Not Found</div>} />
          </Routes>
        </main>
        <Toaster 
          position="bottom-right"
          toastOptions={{
            style: {
              background: '#1a1f2f',
              color: '#fff',
              border: '1px solid rgba(255,255,255,0.1)',
              backdropFilter: 'blur(10px)',
            },
          }}
        />
      </div>
    </Router>
  );
}

export default App;
