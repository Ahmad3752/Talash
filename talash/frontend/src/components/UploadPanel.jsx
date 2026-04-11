import { useState } from 'react';
import client from '../api/client';

function UploadPanel() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [successData, setSuccessData] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const handleFile = (file) => {
    if (!file) return;
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      setErrorMessage('Please select a valid PDF file.');
      setSuccessData(null);
      return;
    }

    setSelectedFile(file);
    setErrorMessage('');
    setSuccessData(null);
  };

  const onDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    const file = event.dataTransfer.files?.[0];
    handleFile(file);
  };

  const onInputChange = (event) => {
    const file = event.target.files?.[0];
    handleFile(file);
  };

  const uploadFile = async () => {
    if (!selectedFile) {
      setErrorMessage('Select a PDF first.');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    setIsUploading(true);
    setErrorMessage('');
    setSuccessData(null);

    try {
      const response = await client.post('/api/cv/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setSuccessData(response.data);
      setSelectedFile(null);
    } catch (error) {
      const detail = error?.response?.data?.detail;
      setErrorMessage(typeof detail === 'string' ? detail : 'Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <section className="panel">
      <h2>Upload CV</h2>
      <p className="muted">Drag a PDF here or click the area to select one file.</p>

      <label
        className={`upload-zone ${isDragging ? 'dragging' : ''}`}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
      >
        <input type="file" accept=".pdf,application/pdf" onChange={onInputChange} />
        <span>Drop PDF here or click to browse</span>
      </label>

      {selectedFile && (
        <div className="file-chip">
          Selected: <strong>{selectedFile.name}</strong>
        </div>
      )}

      <button className="primary-btn" type="button" onClick={uploadFile} disabled={isUploading}>
        {isUploading ? <span className="spinner" /> : 'Upload'}
      </button>

      {successData && (
        <div className="card success-card">
          <h3>Upload Successful</h3>
          <p><strong>Message:</strong> {successData.message}</p>
          <p><strong>Extracted Candidates:</strong> {successData.extracted_candidates}</p>
          <p><strong>Newly Stored Candidates:</strong> {successData.newly_stored_candidates}</p>
          {Array.isArray(successData.errors) && successData.errors.length > 0 && (
            <p><strong>Warnings:</strong> {successData.errors.join(', ')}</p>
          )}
        </div>
      )}

      {errorMessage && (
        <div className="card error-card">
          <h3>Upload Failed</h3>
          <p>{errorMessage}</p>
        </div>
      )}
    </section>
  );
}

export default UploadPanel;
