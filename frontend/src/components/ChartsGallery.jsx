import React from 'react';

export default function ChartsGallery({ charts }) {
    if (!charts) return null;

    const chartEntries = Object.entries(charts);

    if (chartEntries.length === 0) return null;

    return (
        <div className="glass-panel animate-fade-in" style={{ animationDelay: '0.3s' }}>
            <h2 className="text-gradient-accent">Analytics Deep Dive</h2>

            <div className="charts-grid">
                {chartEntries.map(([name, base64], index) => {
                    // Format name from snake_case to Title Case
                    const title = name
                        .split('_')
                        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                        .join(' ');

                    const isFullWidth = name === 'risk_timeline' || name === 'monthly_trend';

                    return (
                        <div
                            key={name}
                            className={`glass-panel chart-container ${isFullWidth ? 'full-width-chart' : ''}`}
                            style={{ padding: '1rem' }}
                        >
                            <h3 style={{ fontSize: '1.2rem', marginBottom: '1rem', textAlign: 'center' }}>
                                {title}
                            </h3>
                            <div style={{ borderRadius: '12px', overflow: 'hidden', background: '#fff' }}>
                                {/* 
                  Assuming the backend returns just the base64 string without the prefix, 
                  but we'll safely add it if missing
                */}
                                <img
                                    src={base64.startsWith('data:image') ? base64 : `data:image/png;base64,${base64}`}
                                    alt={title}
                                    style={{ width: '100%', height: 'auto', display: 'block' }}
                                />
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
