import React from 'react';

export default function Nudges({ monthlyScores }) {
    if (!monthlyScores || monthlyScores.length === 0) return null;

    // Let's just show the latest 3 months to avoid overwhelming the view
    const recentMonths = [...monthlyScores].reverse().slice(0, 3);

    return (
        <div className="glass-panel animate-fade-in" style={{ animationDelay: '0.2s' }}>
            <h2 className="text-gradient-accent">Behavioural Insights & Nudges</h2>
            <p className="text-secondary" style={{ marginBottom: '1.5rem' }}>
                Based on your recent spending habits, here is a personalised breakdown.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {recentMonths.map((month) => {
                    const isHighRisk = month.risk_tier === 'High';
                    const isMediumRisk = month.risk_tier === 'Medium';
                    const riskColor = isHighRisk ? 'var(--accent-red)' : isMediumRisk ? 'var(--accent-orange)' : 'var(--accent-green)';

                    return (
                        <div key={month.month} className="nudge-card">
                            <div className="nudge-header">
                                <h3>{month.month}</h3>
                                <span className="risk-badge" style={{ backgroundColor: riskColor }}>
                                    {month.risk_tier} Risk ({month.impulse_risk_score.toFixed(1)})
                                </span>
                            </div>

                            <div className="profile-label">
                                Profile: <strong>{month.behaviour_profile}</strong>
                            </div>

                            {month.nudges && month.nudges.length > 0 && (
                                <ul className="nudge-list">
                                    {month.nudges.map((nudge, idx) => (
                                        <li key={idx}>{nudge}</li>
                                    ))}
                                </ul>
                            )}
                        </div>
                    );
                })}
            </div>

            <style>{`
        .nudge-card {
          background: rgba(15, 23, 42, 0.4);
          border-left: 4px solid var(--accent-purple);
          border-radius: 0 12px 12px 0;
          padding: 1.5rem;
          transition: transform 0.2s;
        }
        .nudge-card:hover { transform: translateX(5px); }
        .nudge-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.5rem;
        }
        .risk-badge {
          padding: 4px 12px;
          border-radius: 20px;
          color: white;
          font-weight: 600;
          font-size: 0.85rem;
          text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }
        .profile-label {
          color: var(--text-secondary);
          margin-bottom: 1rem;
        }
        .nudge-list {
          list-style: none;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        .nudge-list li {
          background: rgba(255, 255, 255, 0.05);
          padding: 0.8rem 1rem;
          border-radius: 8px;
          font-size: 0.95rem;
          display: flex;
          align-items: flex-start;
          gap: 10px;
        }
        .nudge-list li::before {
          content: '💡';
          flex-shrink: 0;
        }
      `}</style>
        </div>
    );
}
