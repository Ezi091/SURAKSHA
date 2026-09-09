import React from 'react';
import './Header.css';

const Header = ({ systemStatus }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'Warning': return 'status-warning';
      case 'Critical': return 'status-critical';
      case 'Severe': return 'status-severe';
      case 'Evacuation': return 'status-evacuation';
      default: return 'status-normal';
    }
  };

  return (
    <header className="suraksha-header">
      <div className="header-logo-title">
        <div className="logo-placeholder"></div>
        <h1>SURAKSHA <span>Urban Flood Monitoring</span></h1>
      </div>
      <div className="system-status-indicator">
        <span className="status-label">System Status:</span>
        <span className={`status-badge ${getStatusColor(systemStatus)}`}>
          {systemStatus}
        </span>
      </div>
    </header>
  );
};

export default Header;