import React from 'react';

export default function Dashboard({ summary, data }) {
    if (!summary) return null;

    return (
        <div className="wrapped-slide slide-summary animate-fade-in" style={{ animationDelay: '0.1s' }}>
            <div className="slide-content">
                <h3 className="slide-subtitle text-gradient">Statement Analysis</h3>
                <h1 className="slide-title">
                    Processed <br />
                    <span className="text-gradient-alt">{summary.total_transactions}</span> transactions.
                </h1>

                <p className="slide-narrative">
                    Showing insights from <strong>{summary.date_range.replace(' → ', ' and ')}</strong> across <strong>{summary.total_months} months</strong> of financial data.
                </p>

                <div className="big-stats-container">
                    <div className="big-stat">
                        <p className="stat-label">Total Out</p>
                        <h2 className="stat-value text-gradient-accent">
                            ₹{summary.total_withdrawn.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                        </h2>
                    </div>
                    <div className="big-stat">
                        <p className="stat-label">Total In</p>
                        <h2 className="stat-value text-gradient">
                            ₹{summary.total_deposited.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                        </h2>
                    </div>
                </div>
            </div>

            <style>{`
                .wrapped-slide {
                    min-height: 80vh;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    padding: 4rem 2rem;
                    border-radius: var(--glass-radius);
                    position: relative;
                    overflow: hidden;
                    background: var(--glass-bg);
                    backdrop-filter: blur(20px);
                    border: 1px solid var(--glass-border);
                    box-shadow: 0 20px 50px rgba(0,0,0,0.5);
                    margin-bottom: 2rem;
                }
                
                .slide-content {
                    max-width: 800px;
                    margin: 0 auto;
                    width: 100%;
                    position: relative;
                    z-index: 2;
                }
                
                .slide-subtitle {
                    text-transform: uppercase;
                    letter-spacing: 0.15em;
                    font-size: 1rem;
                    margin-bottom: 2rem;
                }
                
                .slide-title {
                    font-size: clamp(3rem, 8vw, 5.5rem);
                    line-height: 1.05;
                    margin-bottom: 2rem;
                }
                
                .slide-narrative {
                    font-size: clamp(1.2rem, 3vw, 1.8rem);
                    color: var(--text-secondary);
                    margin-bottom: 4rem;
                    line-height: 1.4;
                    max-width: 600px;
                }
                
                .big-stats-container {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                    gap: 3rem;
                }
                
                .stat-label {
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                    font-size: 1rem;
                    color: var(--text-tertiary);
                    font-weight: 700;
                    margin-bottom: 0.5rem;
                }
                
                .stat-value {
                    font-size: clamp(2.5rem, 6vw, 4rem);
                }
            `}</style>
        </div>
    );
}
