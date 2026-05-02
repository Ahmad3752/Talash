import { useState } from 'react';
import client from '../api/client';
import { Upload, File, CheckCircle, AlertCircle, Loader2, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';

const UploadPage = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [batchSummary, setBatchSummary] = useState(null);
  const [isDragActive, setIsDragActive] = useState(false);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected && selected.type === 'application/pdf') {
      setFile(selected);
    } else {
      toast.error('Please select a PDF file');
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await client.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setBatchSummary(response.data);
      toast.success('CV Uploaded Successfully!');
      setFile(null);
    } catch (error) {
      console.error('Upload failed:', error);
      toast.error('Upload failed. Please check backend.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto py-10 px-6">
      <div className="mb-10">
        <h1 className="text-4xl mb-2">Ingest Data</h1>
        <p className="text-slate-400">Upload candidate CVs for deep structural analysis and scoring.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <div 
            onDragOver={(e) => { e.preventDefault(); setIsDragActive(true); }}
            onDragLeave={() => setIsDragActive(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragActive(false);
              const droppedFile = e.dataTransfer.files[0];
              if (droppedFile?.type === 'application/pdf') setFile(droppedFile);
            }}
            className={`
              glass-card p-16 flex flex-col items-center justify-center border-dashed border-2 transition-all
              ${isDragActive ? 'border-brand-teal bg-brand-teal/5 scale-[1.02]' : 'border-white/10'}
            `}
          >
            <div className="w-20 h-20 bg-brand-teal/10 text-brand-teal rounded-full flex items-center justify-center mb-6">
              <Upload className="w-10 h-10" />
            </div>
            <h2 className="text-xl mb-2 text-center">Drag & Drop PDF CV</h2>
            <p className="text-slate-500 text-sm mb-8">or click to browse from your device</p>
            
            <input 
              type="file" 
              className="hidden" 
              id="cv-upload" 
              accept=".pdf"
              onChange={handleFileChange}
            />
            <label 
              htmlFor="cv-upload"
              className="bg-brand-teal text-brand-bg px-8 py-3 rounded-xl font-bold cursor-pointer hover:bg-brand-teal/90 transition-colors"
            >
              Select File
            </label>
          </div>

          {file && (
            <div className="mt-6 glass-card p-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-white/5 rounded-lg text-slate-400">
                  <File className="w-6 h-6" />
                </div>
                <div>
                  <div className="font-bold">{file.name}</div>
                  <div className="text-xs text-slate-500 font-mono">{(file.size / 1024).toFixed(1)} KB</div>
                </div>
              </div>
              <button 
                onClick={handleUpload}
                disabled={uploading}
                className="bg-brand-teal text-brand-bg px-6 py-2 rounded-lg font-bold flex items-center gap-2 disabled:opacity-50"
              >
                {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Upload & Process'}
              </button>
            </div>
          )}
        </div>

        <div>
          <div className="glass-card p-6 h-full">
            <h3 className="text-lg mb-6 flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-brand-teal" />
              Batch Summary
            </h3>
            
            {!batchSummary ? (
              <div className="text-center py-10">
                <AlertCircle className="w-12 h-12 text-slate-800 mx-auto mb-4" />
                <p className="text-slate-600 text-sm italic">No recent uploads in this session.</p>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="flex justify-between items-end border-b border-white/5 pb-4">
                  <span className="text-xs text-slate-500 font-mono uppercase">Candidates</span>
                  <span className="text-2xl font-mono font-bold text-brand-teal">{batchSummary.candidates_count || 1}</span>
                </div>
                <div className="flex justify-between items-end border-b border-white/5 pb-4">
                  <span className="text-xs text-slate-500 font-mono uppercase">New Profiles</span>
                  <span className="text-2xl font-mono font-bold text-brand-green">{batchSummary.new_count || 1}</span>
                </div>
                <div className="flex justify-between items-end border-b border-white/5 pb-4">
                  <span className="text-xs text-slate-500 font-mono uppercase">Existing Updated</span>
                  <span className="text-2xl font-mono font-bold text-brand-amber">{batchSummary.existing_count || 0}</span>
                </div>

                <Link 
                  to="/candidates"
                  className="w-full mt-6 py-4 rounded-xl border border-brand-teal/30 text-brand-teal flex items-center justify-center gap-2 font-bold hover:bg-brand-teal/5 transition-all"
                >
                  View Candidates <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadPage;
