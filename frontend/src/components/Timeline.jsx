import React from 'react';
import './Timeline.css';

const Timeline = ({ timeIndex, setTimeIndex, totalHorizons = 4 }) => {
  const steps = [];
  for (let i = 0; i < totalHorizons; i++) {
    steps.push({
      index: i,
      label: `T+${i}${i === 0 ? ' (Now)' : ` (${i}h)`}`
    });
  }

  return (
    <div className="timeline-container">
      <h3>Prediction Timeline</h3>
      <div className="timeline-controls">
        {steps.map(step => (
          <button
            key={step.index}
            className={`timeline-btn ${timeIndex === step.index ? 'active' : ''}`}
            onClick={() => setTimeIndex(step.index)}
          >
            {step.label}
          </button>
        ))}
      </div>
      <div className="timeline-info">
        <p>Showing predicted flood impact for: <strong>{steps[timeIndex]?.label || 'N/A'}</strong></p>
      </div>
    </div>
  );
};

export default Timeline;