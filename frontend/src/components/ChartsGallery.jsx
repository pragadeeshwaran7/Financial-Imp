import React, { useState } from 'react';

export default function ChartsGallery({ charts }) {
    if (!charts) return null;

    const chartEntries = Object.entries(charts);

    if (chartEntries.length === 0) return null;

    const [activeChart, setActiveChart] = useState(chartEntries[0][0]);
    const activeData = charts[activeChart];

    // Support both the old format (just string) and the new format (object with base64 and interpretation)
    const isObject = typeof activeData === 'object' && activeData !== null;
    const activeBase64 = isObject ? activeData.base64 : activeData;
    const activeInterpretation = isObject ? activeData.interpretation : null;

    const activeTitle = activeChart
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');

    return (
        <div className="wrapped-slide slide-charts animate-fade-in" style={{ animationDelay: '0.3s' }}>
            <div className="slide-content">
                <h3 className="slide-subtitle text-gradient">Visual Analysis</h3>
                <h2 className="slide-title" style={{ fontSize: 'clamp(2.5rem, 6vw, 4rem)', marginBottom: '3rem' }}>
                    The numbers in <br /> <span className="text-gradient">detail</span>.
                </h2>

                <div className="chart-selector">
                    {chartEntries.map(([name]) => {
                        const title = name
                            .split('_')
                            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                            .join(' ');
                        return (
                            <button
                                key={name}
                                className={`chart-tab ${activeChart === name ? 'active' : ''}`}
                                onClick={() => setActiveChart(name)}
                            >
                                {title}
                            </button>
                        );
                    })}
                </div>

                <div className="chart-display-card">
                    <h3 className="chart-title">{activeTitle}</h3>

                    {activeInterpretation && (
                        <p className="chart-interpretation">{activeInterpretation}</p>
                    )}

                    <div className="chart-image-wrapper">
                        <img
                            src={activeBase64.startsWith('data:image') ? activeBase64 : `data:image/png;base64,${activeBase64}`}
                            alt={activeTitle}
                        />
                    </div>
                </div>
            </div>

            <style>{`
                .slide-charts {
                    background: linear-gradient(180deg, rgba(46, 119, 208, 0.1) 0%, rgba(18, 18, 18, 1) 100%), var(--bg-dark);
                    min-height: 80vh;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }

                .chart-selector {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 1rem;
                    margin-bottom: 3rem;
                }

                .chart-tab {
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    color: var(--text-secondary);
                    padding: 0.8rem 1.5rem;
                    border-radius: 30px;
                    font-size: 1rem;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }

                .chart-tab:hover {
                    background: rgba(255, 255, 255, 0.1);
                    color: var(--text-primary);
                }

                .chart-tab.active {
                    background: var(--text-primary);
                    color: var(--bg-darker);
                    border-color: var(--text-primary);
                }

                .chart-display-card {
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 20px;
                    padding: 2rem;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    box-shadow: 0 15px 30px rgba(0,0,0,0.4);
                }

                .chart-title {
                    font-size: 1.5rem;
                    text-align: center;
                    margin-bottom: 1rem;
                    color: var(--text-primary);
                    letter-spacing: 0.05em;
                }

                .chart-interpretation {
                    text-align: center;
                    font-size: 1.1rem;
                    color: var(--text-secondary);
                    margin-bottom: 2rem;
                    line-height: 1.5;
                    max-width: 800px;
                    margin-left: auto;
                    margin-right: auto;
                }

                .chart-image-wrapper {
                    border-radius: 12px;
                    overflow: hidden;
                    background: #fff;
                    padding: 1rem;
                }

                .chart-image-wrapper img {
                    width: 100%;
                    height: auto;
                    display: block;
                    mix-blend-mode: multiply;
                }
            `}</style>
        </div>
    );
}
