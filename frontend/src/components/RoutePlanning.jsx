import React, { useState } from 'react';
import './RoutePlanning.css';

const DEMO_LOCATIONS = [
  { id: 'n1', name: 'Downtown (n1)' },
  { id: 'n2', name: 'Hospital (n2)' },
  { id: 'n3', name: 'Airport (n3)' },
  { id: 'n4', name: 'Port (n4)' },
  { id: 'n5', name: 'Suburbs (n5)' },
];

const RoutePlanning = ({ onRouteCalculated, isLoading, error }) => {
  const [origin, setOrigin] = useState('n1');
  const [destination, setDestination] = useState('n5');
  const [depthThreshold, setDepthThreshold] = useState(15);

  const handleFindRoute = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/routing/safe-route', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          origin,
          destination,
          depth_threshold_cm: depthThreshold,
        }),
      });

      if (!response.ok) {
        throw new Error(`Routing failed: ${response.statusText}`);
      }

      const data = await response.json();
      onRouteCalculated(data);
    } catch (err) {
      console.error('Route calculation error:', err);
    }
  };

  return (
    <div className="route-planning">
      <div className="route-header">
        <h3>📍 Safe Route Planning</h3>
        <p className="route-subtitle">Find flood-safe routes</p>
      </div>

      <div className="route-controls">
        <div className="route-input-group">
          <label>Origin</label>
          <select
            value={origin}
            onChange={(e) => setOrigin(e.target.value)}
            disabled={isLoading}
          >
            {DEMO_LOCATIONS.map(loc => (
              <option key={loc.id} value={loc.id}>
                {loc.name}
              </option>
            ))}
          </select>
        </div>

        <div className="route-input-group">
          <label>Destination</label>
          <select
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            disabled={isLoading}
          >
            {DEMO_LOCATIONS.map(loc => (
              <option key={loc.id} value={loc.id}>
                {loc.name}
              </option>
            ))}
          </select>
        </div>

        <div className="route-input-group">
          <label>Water Depth Threshold (cm)</label>
          <input
            type="number"
            min="5"
            max="100"
            step="5"
            value={depthThreshold}
            onChange={(e) => setDepthThreshold(Number(e.target.value))}
            disabled={isLoading}
          />
        </div>
      </div>

      <button
        className="find-route-btn"
        onClick={handleFindRoute}
        disabled={isLoading || origin === destination}
      >
        {isLoading ? 'Finding Route...' : 'Find Safe Route'}
      </button>

      {error && (
        <div className="route-error">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};

export default RoutePlanning;
