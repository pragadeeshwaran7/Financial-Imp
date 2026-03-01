import { useState } from 'react';
import FileUpload from './components/FileUpload';
import Dashboard from './components/Dashboard';
import Nudges from './components/Nudges';
import ChartsGallery from './components/ChartsGallery';
import './App.css';

function App() {
  const [isUploading, setIsUploading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);

  const handleUpload = async (file) => {
    setIsUploading(true);
    setError(null);
    setAnalysisResult(null);

    const formData = new FormData();
    formData.append('statement', file);

    try {
      const response = await fetch('http://localhost:8000/analyse', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to analyze file');
      }

      const data = await response.json();
      console.log('Analysis complete', data);
      setAnalysisResult(data);
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleReset = () => {
    setAnalysisResult(null);
    setError(null);
  };

  return (
    <div className="app-container">
      <div className="container">
        <header className="header animate-fade-in">
          <h1 className="text-gradient">Financial Impulse Analyser</h1>
          <p>
            Upload your bank statement to unlock ML-powered insights into your
            spending behaviours, anomalies, and risk profile.
          </p>
        </header>

        <main className="main-content">
          {error && (
            <div className="glass-panel" style={{ borderLeft: '4px solid var(--accent-red)' }}>
              <h3 style={{ color: 'var(--accent-red)' }}>Error analysing statement</h3>
              <p>{error}</p>
              <button
                onClick={handleReset}
                className="btn-primary"
                style={{ marginTop: '1rem', background: 'var(--accent-red)' }}
              >
                Try Again
              </button>
            </div>
          )}

          {!analysisResult && !error && (
            <div style={{ maxWidth: '800px', margin: '0 auto', width: '100%' }}>
              <FileUpload onUploadComplete={handleUpload} isUploading={isUploading} />
            </div>
          )}

          {analysisResult && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button onClick={handleReset} className="btn-primary" style={{ background: 'var(--glass-bg)', color: 'white' }}>
                  Analyse Another Statement
                </button>
              </div>

              <Dashboard summary={analysisResult.summary} data={analysisResult} />

              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '2rem' }}>
                <Nudges monthlyScores={analysisResult.monthly_scores} />
              </div>

              <ChartsGallery charts={analysisResult.charts} />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
