import { useEffect, useRef, useState } from 'react';
import client from '../api/client';
import { Upload, File, CheckCircle, AlertCircle, ArrowRight, XCircle, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';

const POLL_INTERVAL_MS = 3000;
const RESET_UPLOAD_DELAY_MS = 2500;

const formatScore = (score) => {
  const value = Number(score);
  return Number.isFinite(value) ? value.toFixed(1) : '--';
};

const isFailedStatus = (status) => {
  if (!status) return false;
  const normalized = String(status).toLowerCase();
  return normalized.includes('fail') || normalized.includes('error');
};

const getCandidateScore = (candidate) => candidate?.cv_summary?.overall_score;

const getBatchScore = (entries) => {
  const scores = entries
    .map((entry) => Number(entry.score))
    .filter((score) => Number.isFinite(score));

  if (scores.length === 0) return '--';
  if (scores.length === 1) return formatScore(scores[0]);

  const average = scores.reduce((sum, score) => sum + score, 0) / scores.length;
  return `${formatScore(average)} avg`;
};

const getEntryLabel = (entry) => entry.name || entry.filename || entry.cv_id || 'Candidate CV';

const UploadPage = () => {
  const [file, setFile] = useState(null);
  const [uploadState, setUploadState] = useState('idle');
  const [batchSummary, setBatchSummary] = useState(null);
  const [trackedCandidates, setTrackedCandidates] = useState([]);
  const [processingFile, setProcessingFile] = useState(null);
  const [processingError, setProcessingError] = useState('');
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef(null);
  const pollingTimerRef = useRef(null);
  const resetTimerRef = useRef(null);
  const trackedCandidatesRef = useRef([]);

  const isUploading = uploadState === 'uploading';
  const isProcessing = uploadState === 'processing';
  const isComplete = uploadState === 'complete';
  const isError = uploadState === 'error';
  const isInteractionLocked = isUploading || isProcessing || isComplete;

  const clearPollingTimer = () => {
    if (pollingTimerRef.current) {
      clearInterval(pollingTimerRef.current);
      pollingTimerRef.current = null;
    }
  };

  const clearResetTimer = () => {
    if (resetTimerRef.current) {
      clearTimeout(resetTimerRef.current);
      resetTimerRef.current = null;
    }
  };

  const updateTrackedCandidates = (entries) => {
    trackedCandidatesRef.current = entries;
    setTrackedCandidates(entries);
  };

  const resetUploadArea = () => {
    setFile(null);
    setUploadState('idle');
    setProcessingFile(null);
    setProcessingError('');
    setIsDragActive(false);

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  useEffect(() => {
    return () => {
      if (pollingTimerRef.current) {
        clearInterval(pollingTimerRef.current);
      }

      if (resetTimerRef.current) {
        clearTimeout(resetTimerRef.current);
      }
    };
  }, []);

  const buildTrackedEntries = (uploadData, uploadedFile) => {
    const candidates = Array.isArray(uploadData?.candidates) && uploadData.candidates.length > 0
      ? uploadData.candidates
      : [{ cv_id: uploadData?.candidate_id, preview: uploadData?.message }];

    return candidates.map((candidate, index) => ({
      cv_id: candidate.cv_id || candidate.candidate_id || `upload-${Date.now()}-${index}`,
      filename: uploadedFile.name,
      preview: candidate.preview,
      status: 'processing',
      name: null,
      score: null,
      grade: null,
    }));
  };

  const markProcessingError = (message) => {
    clearPollingTimer();
    setUploadState('error');
    setProcessingError(message);
    updateTrackedCandidates(
      trackedCandidatesRef.current.map((entry) => ({
        ...entry,
        status: 'error',
      }))
    );
  };

  const beginPolling = (initialEntries) => {
    clearPollingTimer();
    clearResetTimer();

    updateTrackedCandidates(initialEntries);

    const pollCandidates = async () => {
      try {
        const response = await client.get('/candidates');
        const candidates = Array.isArray(response.data) ? response.data : [];

        const nextEntries = trackedCandidatesRef.current.map((entry) => {
          const candidate = candidates.find((item) => item.candidate_id === entry.cv_id);

          if (!candidate) {
            return { ...entry, status: 'processing' };
          }

          const apiStatus = candidate.status || candidate.cv_summary?.overall_status;

          if (isFailedStatus(apiStatus)) {
            return {
              ...entry,
              status: 'error',
              dbId: candidate.id,
              name: candidate.name || entry.name,
              email: candidate.email || entry.email,
            };
          }

          if (candidate.cv_summary) {
            return {
              ...entry,
              status: 'verified',
              dbId: candidate.id,
              name: candidate.name || entry.name,
              email: candidate.email || entry.email,
              score: getCandidateScore(candidate),
              grade: candidate.cv_summary.overall_grade,
            };
          }

          return {
            ...entry,
            status: 'processing',
            dbId: candidate.id,
            name: candidate.name || entry.name,
            email: candidate.email || entry.email,
          };
        });

        updateTrackedCandidates(nextEntries);

        const hasError = nextEntries.some((entry) => entry.status === 'error');
        if (hasError) {
          markProcessingError('Processing failed. Please retry the upload.');
          toast.error('Processing failed. Please retry.');
          return;
        }

        const allVerified = nextEntries.length > 0 && nextEntries.every((entry) => entry.status === 'verified');
        if (allVerified) {
          clearPollingTimer();
          setUploadState('complete');
          toast.success(`CV processed successfully. Score: ${getBatchScore(nextEntries)}`);

          resetTimerRef.current = setTimeout(() => {
            resetUploadArea();
          }, RESET_UPLOAD_DELAY_MS);
        }
      } catch (error) {
        console.error('Polling failed:', error);
        markProcessingError('Unable to check processing status. Please retry the upload.');
        toast.error('Processing failed. Please retry.');
      }
    };

    pollingTimerRef.current = setInterval(pollCandidates, POLL_INTERVAL_MS);
    pollCandidates();
  };

  const handleFileChange = (e) => {
    if (isInteractionLocked) return;

    const selected = e.target.files[0];
    if (selected && selected.type === 'application/pdf') {
      setFile(selected);
      setUploadState('idle');
      setProcessingError('');
    } else {
      toast.error('Please select a PDF file');
    }
  };

  const handleUpload = async () => {
    if (!file || isInteractionLocked) return;

    clearPollingTimer();
    clearResetTimer();
    setUploadState('uploading');
    setProcessingFile({ name: file.name, size: file.size });
    setProcessingError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await client.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const entries = buildTrackedEntries(response.data, file);
      setBatchSummary({ ...response.data, filename: file.name });
      updateTrackedCandidates(entries);
      setFile(null);
      setUploadState('processing');
      toast.success('CV uploaded. Processing started.');
      beginPolling(entries);

      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      console.error('Upload failed:', error);
      const detail = error?.response?.data?.detail;
      setUploadState('error');
      setProcessingError(detail || 'Upload failed. Please check backend.');
      updateTrackedCandidates([
        {
          cv_id: `failed-${Date.now()}`,
          filename: file.name,
          status: 'error',
          name: null,
          score: null,
          grade: null,
        },
      ]);
      toast.error('Upload failed. Please check backend.');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragActive(false);

    if (isInteractionLocked) return;

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile?.type === 'application/pdf') {
      setFile(droppedFile);
      setUploadState('idle');
      setProcessingError('');
    } else {
      toast.error('Please drop a PDF file');
    }
  };

  const handleRetry = () => {
    resetUploadArea();
    setTimeout(() => fileInputRef.current?.click(), 0);
  };

  const primaryEntry = trackedCandidates.find((entry) => entry.status === 'verified') || trackedCandidates[0];
  const completedCount = trackedCandidates.filter((entry) => entry.status === 'verified').length;
  const dropzoneTone = isError
    ? 'border-brand-rose/50 bg-brand-rose/5'
    : isComplete
      ? 'border-brand-green/50 bg-brand-green/5'
      : isUploading || isProcessing
        ? 'border-brand-teal/60 bg-brand-teal/5'
        : isDragActive
          ? 'border-brand-teal bg-brand-teal/5 scale-[1.02]'
          : 'border-white/10';

  return (
    <div className="max-w-5xl mx-auto py-10 px-6">
      <div className="mb-10">
        <h1 className="text-4xl mb-2" style={{ color: 'var(--text-primary)' }}>Ingest Data</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Upload candidate CVs for deep structural analysis and scoring.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <div 
            onDragOver={(e) => {
              e.preventDefault();
              if (!isInteractionLocked) setIsDragActive(true);
            }}
            onDragLeave={() => setIsDragActive(false)}
            onDrop={handleDrop}
            className={`
              glass-card min-h-[430px] p-16 flex flex-col items-center justify-center border-dashed border-2 transition-all
              ${dropzoneTone}
            `}
          >
            {isUploading || isProcessing ? (
              <>
                <div className="cv-processing-pulse w-24 h-24 bg-brand-teal/10 text-brand-teal rounded-full flex items-center justify-center mb-6">
                  <div className="cv-processing-spinner" aria-hidden="true" />
                </div>
                <h2 className="text-xl mb-2 text-center" style={{ color: 'var(--text-primary)' }}>
                  {isUploading ? 'Uploading CV...' : 'Processing CV...'}
                </h2>
                <p className="text-sm mb-8 text-center max-w-md truncate" style={{ color: 'var(--text-muted)' }}>
                  {primaryEntry?.name || processingFile?.name || primaryEntry?.filename || 'Candidate CV'}
                </p>
              </>
            ) : isComplete ? (
              <>
                <div className="w-24 h-24 bg-brand-green/10 text-brand-green rounded-full flex items-center justify-center mb-6">
                  <CheckCircle className="w-12 h-12" />
                </div>
                <h2 className="text-xl mb-2 text-center" style={{ color: 'var(--text-primary)' }}>Analysis Complete!</h2>
                <div className="text-sm text-center mb-8 space-y-1" style={{ color: 'var(--text-muted)' }}>
                  <p>{trackedCandidates.length > 1 ? `${completedCount} candidates analyzed` : getEntryLabel(primaryEntry || {})}</p>
                  <p className="font-mono text-brand-green">Score received: {getBatchScore(trackedCandidates)}</p>
                </div>
              </>
            ) : isError ? (
              <>
                <div className="w-24 h-24 bg-brand-rose/10 text-brand-rose rounded-full flex items-center justify-center mb-6">
                  <XCircle className="w-12 h-12" />
                </div>
                <h2 className="text-xl mb-2 text-center" style={{ color: 'var(--text-primary)' }}>Processing Failed</h2>
                <p className="text-sm mb-8 text-center max-w-md" style={{ color: 'var(--text-muted)' }}>
                  {processingError || 'Something went wrong while processing this CV.'}
                </p>
              </>
            ) : (
              <>
                <div className="w-20 h-20 bg-brand-teal/10 text-brand-teal rounded-full flex items-center justify-center mb-6">
                  <Upload className="w-10 h-10" />
                </div>
                <h2 className="text-xl mb-2 text-center" style={{ color: 'var(--text-primary)' }}>Drag & Drop PDF CV</h2>
                <p className="text-sm mb-8" style={{ color: 'var(--text-muted)' }}>or click to browse from your device</p>
              </>
            )}
            
            <input 
              type="file" 
              className="hidden" 
              id="cv-upload" 
              accept=".pdf"
              ref={fileInputRef}
              disabled={isInteractionLocked}
              onChange={handleFileChange}
            />
            {isError ? (
              <button
                type="button"
                onClick={handleRetry}
                className="bg-brand-teal text-brand-bg px-8 py-3 rounded-xl font-bold flex items-center gap-2 hover:bg-brand-teal/90 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Retry Upload
              </button>
            ) : (
              <label
                htmlFor="cv-upload"
                aria-disabled={isInteractionLocked}
                className={`bg-brand-teal text-brand-bg px-8 py-3 rounded-xl font-bold transition-colors ${
                  isInteractionLocked
                    ? 'cursor-not-allowed opacity-50'
                    : 'cursor-pointer hover:bg-brand-teal/90'
                }`}
              >
                Select File
              </label>
            )}
          </div>

          {file && uploadState === 'idle' && (
            <div className="mt-6 glass-card p-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-white/5 rounded-lg" style={{ color: 'var(--text-muted)' }}>
                  <File className="w-6 h-6" />
                </div>
                <div>
                  <div className="font-bold" style={{ color: 'var(--text-primary)' }}>{file.name}</div>
                  <div className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>{(file.size / 1024).toFixed(1)} KB</div>
                </div>
              </div>
              <button 
                onClick={handleUpload}
                disabled={isInteractionLocked}
                className="bg-brand-teal text-brand-bg px-6 py-2 rounded-lg font-bold flex items-center gap-2 disabled:opacity-50"
              >
                Upload & Process
              </button>
            </div>
          )}
        </div>

        <div>
          <div className="glass-card p-6 h-full">
            <h3 className="text-lg mb-6 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
              <CheckCircle className="w-5 h-5 text-brand-teal" />
              Batch Summary
            </h3>
            
            {!batchSummary ? (
              <div className="text-center py-10">
                <AlertCircle className="w-12 h-12 mx-auto mb-4" style={{ color: 'var(--bg-border)' }} />
                <p className="text-sm italic" style={{ color: 'var(--text-muted)' }}>No recent uploads in this session.</p>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="flex justify-between items-end border-b border-white/5 pb-4">
                  <span className="text-xs font-mono uppercase" style={{ color: 'var(--text-muted)' }}>Candidates</span>
                  <span className="text-2xl font-mono font-bold text-brand-teal">{batchSummary.candidates_count ?? 1}</span>
                </div>
                <div className="flex justify-between items-end border-b border-white/5 pb-4">
                  <span className="text-xs font-mono uppercase" style={{ color: 'var(--text-muted)' }}>New Profiles</span>
                  <span className="text-2xl font-mono font-bold text-brand-green">{batchSummary.new_count ?? 0}</span>
                </div>
                <div className="flex justify-between items-end border-b border-white/5 pb-4">
                  <span className="text-xs font-mono uppercase" style={{ color: 'var(--text-muted)' }}>Existing Updated</span>
                  <span className="text-2xl font-mono font-bold text-brand-amber">{batchSummary.existing_count ?? 0}</span>
                </div>

                {trackedCandidates.length > 0 && (
                  <div className="space-y-3">
                    <div className="text-xs font-mono uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
                      Files
                    </div>
                    {trackedCandidates.map((entry) => {
                      const isEntryVerified = entry.status === 'verified';
                      const isEntryError = entry.status === 'error';

                      return (
                        <div key={entry.cv_id} className="rounded-lg border border-white/10 bg-white/[0.03] p-3">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <div className="text-sm font-bold truncate" style={{ color: 'var(--text-primary)' }}>
                                {entry.filename}
                              </div>
                              <div className="text-xs truncate" style={{ color: 'var(--text-muted)' }}>
                                {entry.name || entry.preview || entry.cv_id}
                              </div>
                            </div>
                            <div
                              className={`shrink-0 inline-flex items-center gap-1.5 rounded-full border px-2 py-1 text-[10px] font-mono font-bold uppercase ${
                                isEntryError
                                  ? 'border-brand-rose/40 bg-brand-rose/10 text-brand-rose'
                                  : isEntryVerified
                                    ? 'border-brand-green/40 bg-brand-green/10 text-brand-green'
                                    : 'border-brand-amber/40 bg-brand-amber/10 text-brand-amber'
                              }`}
                            >
                              {isEntryError ? (
                                <XCircle className="w-3 h-3" />
                              ) : isEntryVerified ? (
                                <CheckCircle className="w-3 h-3" />
                              ) : (
                                <span className="cv-status-spinner" aria-hidden="true" />
                              )}
                              {isEntryError ? 'FAILED' : isEntryVerified ? 'VERIFIED' : 'PROCESSING'}
                            </div>
                          </div>
                          {isEntryVerified && (
                            <div className="mt-3 flex items-center justify-between border-t border-white/5 pt-3">
                              <span className="text-xs font-mono uppercase" style={{ color: 'var(--text-muted)' }}>Score</span>
                              <span className="font-mono font-bold text-brand-green">{formatScore(entry.score)}</span>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}

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
