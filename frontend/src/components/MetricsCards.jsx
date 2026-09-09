import React from 'react';
import './MetricsCards.css';

const MetricsCards = ({ metrics }) => {
  return (
    <div className="metrics-container">
      <div className="metric-card">
        <h3>Current Rainfall</h3>
        <div className="metric-value">{metrics.rainfall}</div>
      </div>

      <div className="metric-card warning">
        <h3>Drainage Utilization</h3>
        <div className="metric-value">{metrics.drainage}</div>
        <div className="metric-subtext">Over Capacity!</div>
      </div>

      <div className="metric-card alert">
        <h3>Max Predicted Depth</h3>
        <div className="metric-value">{metrics.maxDepth}</div>
      </div>

      <div className="metric-card danger">
        <h3>High-Risk Locations</h3>
        <div className="metric-value">{metrics.highRiskLocations}</div>
      </div>
    </div>
  );
};

export default MetricsCards;