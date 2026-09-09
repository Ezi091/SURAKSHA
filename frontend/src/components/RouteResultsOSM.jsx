import React from 'react';
import './RouteResultsOSM.css';

const RouteResultsOSM = ({ route, isLoading }) => {
  if (!route) {
    return null;
  }

  if (route.error) {
    return (
      <div className="route-results-osm error">
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

  const isSafe = !route.needs_rerouting;

  return (
    <div className="route-results-osm">
      <div className="results-header">
        <h3>🗺️ Route Analysis</h3>
        {isSafe ? (
          <span className="safe-badge safety-status">✅ SAFE ROUTE</span>
        ) : (
          <span className="reroute-badge safety-status">⚠️ UNSAFE ROUTE</span>
        )}
      </div>

      <div className="results-reason">
        <p><strong>Status:</strong> {route.reason}</p>
      </div>

      {isSafe ? (
        // SAFE ROUTE DISPLAY
        <div className="route-single-safe">
          <div className="route-card safe-only">
            <div className="route-card-header">
              <h4>✅ Route is Safe</h4>
              <span className="safe-indicator">No flood risk detected</span>
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
                {normalRoute.risk_levels.slice(0, 5).map((risk, idx) => (
                  <span key={idx} className={`risk-badge ${risk.toLowerCase()}`}>
                    {risk}
                  </span>
                ))}
                {normalRoute.risk_levels.length > 5 && (
                  <span className="risk-badge-more">+{normalRoute.risk_levels.length - 5}</span>
                )}
              </div>
            </div>

            {normalRoute.road_summary && (
              <div className="route-roads">
                <span className="stat-label">Roads:</span>
                <p className="road-names">{normalRoute.road_summary}</p>
              </div>
            )}
          </div>
        </div>
      ) : (
        // UNSAFE ROUTE DISPLAY - Show both routes
        <div className="route-comparison">
          {/* Normal Route Card (Red - Unsafe) */}
          <div className="route-card normal">
            <div className="route-card-header">
              <h4>⚠️ Original Route</h4>
              {normalRoute.has_high_risk && (
                <span className="risk-warning">Flood Risk</span>
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
                {normalRoute.risk_levels.slice(0, 5).map((risk, idx) => (
                  <span key={idx} className={`risk-badge ${risk.toLowerCase()}`}>
                    {risk}
                  </span>
                ))}
                {normalRoute.risk_levels.length > 5 && (
                  <span className="risk-badge-more">+{normalRoute.risk_levels.length - 5}</span>
                )}
              </div>
            </div>

            {normalRoute.road_summary && (
              <div className="route-roads">
                <span className="stat-label">Roads:</span>
                <p className="road-names">{normalRoute.road_summary}</p>
              </div>
            )}
          </div>

          {/* Safe Route Card (Green - Recommended) */}
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
                {safeRoute.risk_levels.slice(0, 5).map((risk, idx) => (
                  <span key={idx} className={`risk-badge ${risk.toLowerCase()}`}>
                    {risk}
                  </span>
                ))}
                {safeRoute.risk_levels.length > 5 && (
                  <span className="risk-badge-more">+{safeRoute.risk_levels.length - 5}</span>
                )}
              </div>
            </div>

            {safeRoute.road_summary && (
              <div className="route-roads">
                <span className="stat-label">Roads:</span>
                <p className="road-names">{safeRoute.road_summary}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Affected Segments Summary (only show if rerouting) */}
      {!isSafe && (
        <div className="affected-segments">
          <div className="affected-group">
            <h4>⛔ Flooded/High-Risk Segments Avoided</h4>
            {route.avoided_segments.length > 0 ? (
              <div className="segment-list">
                {route.avoided_segments.slice(0, 8).map((seg, idx) => (
                  <span key={idx} className="segment-avoided">{seg}</span>
                ))}
                {route.avoided_segments.length > 8 && (
                  <span className="segment-more">+{route.avoided_segments.length - 8} more</span>
                )}
              </div>
            ) : (
              <p className="no-data">None - original route is safe</p>
            )}
          </div>

          {route.affected_segments.length > 0 && (
            <div className="affected-group">
              <h4>📍 Shared Segments</h4>
              <div className="segment-list">
                {route.affected_segments.slice(0, 8).map((seg, idx) => (
                  <span key={idx} className="segment-shared">{seg}</span>
                ))}
                {route.affected_segments.length > 8 && (
                  <span className="segment-more">+{route.affected_segments.length - 8} more</span>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {isLoading && (
        <div className="loading-overlay">
          <div className="spinner">🔄</div>
        </div>
      )}
    </div>
  );
};

export default RouteResultsOSM;
