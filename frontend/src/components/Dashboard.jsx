import React from 'react';

export default function Dashboard({ summary, data }) {
    if (!summary) return null;

    return (
        <div className="glass-panel animate-fade-in" style={{ animationDelay: '0.1s' }}>
            <h2 className="text-gradient-accent">Financial Summary</h2>

            <div className="dashboard-grid">
                <div className="glass-panel stat-card">
                    <p className="text-secondary">Date Range</p>
                    <h3>{summary.date_range.replace(' → ', ' to ')}</h3>
                    <p className="text-tertiary text-sm">{summary.total_months} months analyzed</p>
                </div>

                <div className="glass-panel stat-card">
                    <p className="text-secondary">Total Processed</p>
                    <div className="flex-row">
                        <div>
                            <p className="text-xs text-green">Deposits</p>
                            <h3>₹{summary.total_deposited.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</h3>
                        </div>
                        <div>
                            <p className="text-xs text-red">Withdrawals</p>
                            <h3>₹{summary.total_withdrawn.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</h3>
                        </div>
                    </div>
                </div>

                <div className="glass-panel stat-card">
                    <p className="text-secondary">Transactions</p>
                    <h3>{summary.total_transactions}</h3>
                    <p className="text-tertiary text-sm">Valid rows processed</p>
                </div>
            </div>

            <style>{`
        .stat-card {
          padding: 1.5rem;
          background: rgba(30, 41, 59, 0.6);
        }
        .stat-card h3 {
          font-size: 1.5rem;
          margin-top: 0.5rem;
          margin-bottom: 0.2rem;
        }
        .text-sm { font-size: 0.85rem; }
        .text-xs { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; }
        .flex-row { display: flex; gap: 2rem; margin-top: 0.5rem; }
        .text-green { color: var(--accent-green); }
        .text-red { color: var(--accent-red); }
      `}</style>
        </div>
    );
}
