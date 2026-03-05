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
      const response = await fetch('/analyse', {
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
      {/* Landing/Upload Section */}
      {!analysisResult && (
        <div className="landing-section animate-fade-in">
          <div className="container" style={{ textAlign: 'center' }}>
            <h1 className="text-gradient" style={{ marginBottom: '1rem' }}>Your Financial Identity</h1>
            <p style={{ fontSize: '1.2rem', color: 'var(--text-secondary)', marginBottom: '3rem', maxWidth: '600px', margin: '0 auto 3rem auto' }}>
              Upload your bank statement to unlock a bold, personalized narrative of your spending behaviour, anomalies, and risk profile.
            </p>

            {error && (
              <div className="glass-panel" style={{ borderLeft: '4px solid var(--accent-red)', marginBottom: '2rem', textAlign: 'left' }}>
                <h3 style={{ color: 'var(--accent-red)' }}>Error analysing statement</h3>
                <p>{error}</p>
                <button
                  onClick={handleReset}
                  className="btn-primary"
                  style={{ marginTop: '1rem', background: 'var(--accent-red)', color: 'white' }}
                >
                  Try Again
                </button>
              </div>
            )}

            {!error && (
              <div style={{ maxWidth: '600px', margin: '0 auto', width: '100%' }}>
                <FileUpload onUploadComplete={handleUpload} isUploading={isUploading} />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Wrapped Results Flow */}
      {analysisResult && (
        <main className="wrapped-flow">
          <div style={{ position: 'sticky', top: '1rem', right: '1rem', zIndex: 100, display: 'flex', justifyContent: 'flex-end', paddingRight: '2rem' }}>
            <button onClick={handleReset} className="btn-primary" style={{ background: 'var(--glass-bg)', color: 'white', border: '1px solid rgba(255,255,255,0.2)' }}>
              Start Over
            </button>
          </div>

          <div className="container" style={{ maxWidth: '1000px', margin: '0 auto' }}>
            <Dashboard summary={analysisResult.summary} data={analysisResult} />
            <Nudges monthlyScores={analysisResult.monthly_scores} />
            <ChartsGallery charts={analysisResult.charts} />
          </div>
        </main>
      )}

      <style>{`
        .landing-section {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 2rem;
        }
        
        .wrapped-flow {
          padding-bottom: 5rem;
        }
      `}</style>
    </div>
  );
}

export default App;
