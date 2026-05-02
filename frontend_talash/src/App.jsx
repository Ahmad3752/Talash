import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import AppSidebar from './components/AppSidebar';
import UploadPage from './pages/UploadPage';
import CandidatesPage from './pages/CandidatesPage';
import CandidateDetailPage from './pages/CandidateDetailPage';

function App() {
  return (
    <Router>
      <div className="flex min-h-screen bg-brand-bg">
        <AppSidebar />
        <main className="flex-1 ml-64 min-h-screen">
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/candidates" element={<CandidatesPage />} />
            <Route path="/candidates/:id" element={<CandidateDetailPage />} />
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
