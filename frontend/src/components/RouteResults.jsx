import React from 'react';
import './RouteResults.css';

const RouteResults = ({ route }) => {
  if (!route) {
    return null;
  }

  if (route.error) {
    return (
      <div className="route-results error">
        <h4>❌ Routing Error</h4>
        <p>{route.error}</p>
      </div>
    );
  }

  const normalRoute = route.normal_route;
  const safeRoute = route.safe_route;
  const distanceIncrease = route.distance_increase_km;
  const percentIncrease = normalRoute.distance_km > 0
    ? ((distanceIncrease / normalRoute.distance_km) * 100).toFixed(1)
    : 0;

  return (
    <div className="route-results">
      <div className="results-header">
        <h3>🗺️ Route Analysis</h3>
        {route.needs_rerouting ? (
          <span className="reroute-badge">Rerouting Recommended</span>
        ) : (
          <span className="safe-badge">Original Route is Safe</span>
        )}
      </div>

      <div className="results-reason">
        <p><strong>Status:</strong> {route.reason}</p>
      </div>

      <div className="route-comparison">
        {/* Normal Route */}
        <div className="route-card normal">
          <div className="route-card-header">
            <h4>📍 Original Route</h4>
            {normalRoute.has_high_risk && (
              <span className="risk-warning">⚠️ High Risk</span>
            )}
          </div>

          <div className="route-stat">
            <span className="stat-label">Distance:</span>
            <span className="stat-value">{normalRoute.distance_km} km</span>
          </div>

          <div className="route-stat">
            <span className="stat-label">Segments:</span>
            <span className="stat-value">{normalRoute.segment_ids.length}</span>
          </div>

          <div className="route-stat">
            <span className="stat-label">Max Water Depth:</span>
            <span className="stat-value">{normalRoute.max_water_depth_cm} cm</span>
          </div>

          <div className="route-risks">
            <span className="stat-label">Risk Levels:</span>
            <div className="risk-badges">
              {normalRoute.risk_levels.map((risk, idx) => (
                <span key={idx} className={`risk-badge ${risk.toLowerCase()}`}>
                  {risk}
                </span>
              ))}
            </div>
          </div>

          <div className="route-segments">
            <span className="stat-label">Segments:</span>
            <div className="segment-list">
              {normalRoute.segment_ids.map((seg, idx) => (
                <span key={idx} className="segment-tag">{seg}</span>
              ))}
            </div>
          </div>
        </div>

        {/* Safe Route */}
        <div className="route-card safe">
          <div className="route-card-header">
            <h4>🛡️ Recommended Safe Route</h4>
            <span className="safe-indicator">✓ Safe</span>
          </div>

          <div className="route-stat">
            <span className="stat-label">Distance:</span>
            <span className="stat-value">{safeRoute.distance_km} km</span>
          </div>

          {distanceIncrease > 0 && (
            <div className="route-stat highlight">
              <span className="stat-label">Extra Distance:</span>
              <span className="stat-value">+{distanceIncrease} km ({percentIncrease}%)</span>
            </div>
          )}

          <div className="route-stat">
            <span className="stat-label">Segments:</span>
            <span className="stat-value">{safeRoute.segment_ids.length}</span>
          </div>

          <div className="route-stat">
            <span className="stat-label">Max Water Depth:</span>
            <span className="stat-value">{safeRoute.max_water_depth_cm} cm</span>
          </div>

          <div className="route-risks">
            <span className="stat-label">Risk Levels:</span>
            <div className="risk-badges">
              {safeRoute.risk_levels.map((risk, idx) => (
                <span key={idx} className={`risk-badge ${risk.toLowerCase()}`}>
                  {risk}
                </span>
              ))}
            </div>
          </div>

          <div className="route-segments">
            <span className="stat-label">Segments:</span>
            <div className="segment-list">
              {safeRoute.segment_ids.map((seg, idx) => (
                <span key={idx} className="segment-tag">{seg}</span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Affected Segments */}
      <div className="affected-segments">
        <div className="affected-group">
          <h4>⛔ Flooded Segments Avoided</h4>
          {route.avoided_segments.length > 0 ? (
            <div className="segment-list">
              {route.avoided_segments.map((seg, idx) => (
                <span key={idx} className="segment-avoided">{seg}</span>
              ))}
            </div>
          ) : (
            <p className="no-data">None - original route is safe</p>
          )}
        </div>

        {route.affected_segments.length > 0 && (
          <div className="affected-group">
            <h4>📍 Shared Segments</h4>
            <div className="segment-list">
              {route.affected_segments.map((seg, idx) => (
                <span key={idx} className="segment-shared">{seg}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RouteResults;
