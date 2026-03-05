import React from 'react';

export default function Nudges({ monthlyScores }) {
  if (!monthlyScores || monthlyScores.length === 0) return null;

  // Let's just show the latest 3 months to avoid overwhelming the view
  const recentMonths = [...monthlyScores].reverse().slice(0, 3);

  return (
    <div className="wrapped-slide slide-nudges animate-fade-in" style={{ animationDelay: '0.2s' }}>
      <div className="slide-content">
        <h3 className="slide-subtitle text-gradient">Behavioural Insights</h3>
        <h2 className="slide-title" style={{ fontSize: 'clamp(2.5rem, 6vw, 4rem)', marginBottom: '3rem' }}>
          Recent <span className="text-gradient-accent">Trends</span> and Nudges.
        </h2>

        <div className="tracks-container">
          {recentMonths.map((month, index) => {
            const isHighRisk = month.risk_tier === 'High';
            const isMediumRisk = month.risk_tier === 'Medium';
            const riskClass = isHighRisk ? 'risk-high' : isMediumRisk ? 'risk-medium' : 'risk-low';

            return (
              <div key={month.month} className="track-card">
                <div className="track-number">{(index + 1).toString().padStart(2, '0')}</div>
                <div className="track-details">
                  <div className="track-header">
                    <h3>{month.month}</h3>
                    <span className={`risk-badge ${riskClass}`}>
                      {month.risk_tier} Risk
                    </span>
                  </div>
                  <div className="profile-label">
                    <span style={{ opacity: 0.7 }}>Profile: </span>
                    <strong>{month.behaviour_profile}</strong>
                  </div>

                  {month.nudges && month.nudges.length > 0 && (
                    <ul className="nudge-list">
                      {month.nudges.map((nudge, idx) => (
                        <li key={idx}>{nudge}</li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <style>{`
                .slide-nudges {
                    background: linear-gradient(180deg, rgba(140, 103, 171, 0.1) 0%, rgba(18, 18, 18, 1) 100%), var(--bg-dark);
                }

                .tracks-container {
                    display: flex;
                    flex-direction: column;
                    gap: 1.5rem;
                }

                .track-card {
                    display: flex;
                    gap: 1.5rem;
                    padding: 1.5rem;
                    background: rgba(255, 255, 255, 0.03);
                    border-radius: 16px;
                    transition: transform 0.2s, background 0.2s;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                }

                .track-card:hover { 
                    transform: translateX(10px); 
                    background: rgba(255, 255, 255, 0.08);
                }

                .track-number {
                    font-size: 2rem;
                    font-weight: 900;
                    color: rgba(255, 255, 255, 0.2);
                    width: 40px;
                    text-align: right;
                    flex-shrink: 0;
                }

                .track-details {
                    flex-grow: 1;
                }

                .track-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 0.5rem;
                }

                .track-header h3 {
                    font-size: 1.6rem;
                    margin: 0;
                }

                .risk-badge {
                    padding: 6px 16px;
                    border-radius: 30px;
                    color: white;
                    font-weight: 800;
                    font-size: 0.8rem;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }

                .risk-high { background: var(--accent-red); }
                .risk-medium { background: var(--accent-orange); color: #000; }
                .risk-low { background: var(--accent-green); color: #000; }

                .profile-label {
                    font-size: 1.1rem;
                    color: var(--text-primary);
                    margin-bottom: 1.5rem;
                }

                .nudge-list {
                    list-style: none;
                    display: flex;
                    flex-direction: column;
                    gap: 0.5rem;
                }

                .nudge-list li {
                    background: rgba(255, 255, 255, 0.05);
                    padding: 1rem 1.2rem;
                    border-radius: 12px;
                    font-size: 0.95rem;
                    display: flex;
                    align-items: flex-start;
                    gap: 12px;
                    line-height: 1.4;
                }

                .nudge-list li::before {
                    content: '💡';
                    flex-shrink: 0;
                    font-size: 1.2rem;
                }
            `}</style>
    </div>
  );
}
