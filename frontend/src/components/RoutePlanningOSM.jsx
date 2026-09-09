import React, { useState, useEffect } from 'react';
import { floodApi } from '../services/floodApi';
import CustomLocationSelect from './CustomLocationSelect';
import './RoutePlanningOSM.css';

const RoutePlanningOSM = ({
  onRouteCalculated,
  isLoading,
  error,
  currentPrediction,
  predictions
}) => {
  const [landmarks, setLandmarks] = useState([]);
  const [origin, setOrigin] = useState(null);
  const [destination, setDestination] = useState(null);
  const [depthThreshold, setDepthThreshold] = useState(15);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState(null);

  // Load landmarks on mount
  useEffect(() => {
    const loadLandmarks = async () => {
      try {
        const response = await floodApi.getLandmarks();
        if (response.landmarks && response.landmarks.length > 0) {
          setLandmarks(response.landmarks);
          // Set default origin and destination
          if (response.landmarks.length >= 2) {
            setOrigin(response.landmarks[0]);
            setDestination(response.landmarks[Math.min(1, response.landmarks.length - 1)]);
          }
        }
      } catch (err) {
        console.error('Failed to load landmarks:', err);
      }
    };
    loadLandmarks();
  }, []);

  // Build flood zones from current prediction
  const getFloodZonesFromPrediction = () => {
    if (!currentPrediction || !predictions) {
      return [];
    }

    // Create demo flood zones based on prediction
    const risk = currentPrediction.flood_risk?.toLowerCase() || 'low';
    const depth = currentPrediction.predicted_water_depth_cm || 0;

    if (risk === 'low' && depth < 15) {
      return [];
    }

    // Map zones to Mumbai area based on risk level
    const zones = [
      {
        coordinates: [19.0800, 72.8800],
        radius: 500 + (depth * 10),
        risk: risk,
        depth: depth
      }
    ];

    return zones;
  };

  const handleFindRoute = async () => {
    if (!origin || !destination) {
      setApiError('Please select both origin and destination');
      return;
    }

    if (origin.lat === destination.lat && origin.lon === destination.lon) {
      setApiError('Origin and destination must be different');
      return;
    }

    setLoading(true);
    setApiError(null);

    try {
      const floodZones = getFloodZonesFromPrediction();

      const request = {
        origin_lat: origin.lat,
        origin_lon: origin.lon,
        destination_lat: destination.lat,
        destination_lon: destination.lon,
        depth_threshold_cm: depthThreshold,
        flood_zones: floodZones
      };

      const response = await floodApi.calculateSafeRoute(request);

      if (response.error) {
        setApiError(response.error);
      } else {
        onRouteCalculated(response);
      }
    } catch (err) {
      console.error('Route calculation error:', err);
      setApiError(`Route calculation failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSwapOriginDest = () => {
    const temp = origin;
    setOrigin(destination);
    setDestination(temp);
  };

  return (
    <div className="route-planning-osm">
      <div className="route-header">
        <h3>🛣️ Safe Route Planning</h3>
        <p className="route-subtitle">OSM-based flood-aware navigation</p>
      </div>

      <div className="route-controls">
        <div className="route-input-group">
          <CustomLocationSelect
            label="📍 Origin"
            value={origin ? landmarks.indexOf(origin) : ''}
            onChange={(idx) => setOrigin(landmarks[idx])}
            options={landmarks}
            disabled={loading || landmarks.length === 0}
            placeholder="Select origin..."
          />
        </div>

        <button
          className="swap-btn"
          onClick={handleSwapOriginDest}
          disabled={!origin || !destination || loading}
          title="Swap origin and destination"
        >
          ⇅
        </button>

        <div className="route-input-group">
          <CustomLocationSelect
            label="📍 Destination"
            value={destination ? landmarks.indexOf(destination) : ''}
            onChange={(idx) => setDestination(landmarks[idx])}
            options={landmarks}
            disabled={loading || landmarks.length === 0}
            placeholder="Select destination..."
          />
        </div>

        <div className="route-input-group">
          <label>💧 Depth Threshold (cm)</label>
          <input
            type="number"
            min="5"
            max="100"
            step="5"
            value={depthThreshold}
            onChange={(e) => setDepthThreshold(Number(e.target.value))}
            disabled={loading}
            className="depth-input"
          />
        </div>
      </div>

      <button
        className="find-route-btn"
        onClick={handleFindRoute}
        disabled={loading || !origin || !destination || origin === destination}
      >
        {loading ? '🔄 Finding Route...' : '🗺️ Find Safe Route'}
      </button>

      {apiError && (
        <div className="route-error">
          <span className="error-icon">⚠️</span>
          <span>{apiError}</span>
        </div>
      )}

      {currentPrediction && (
        <div className="route-info-mini">
          <span className="flood-status">
            Flood Risk: <strong>{currentPrediction.flood_risk}</strong>
            ({currentPrediction.predicted_water_depth_cm?.toFixed(1)}cm)
          </span>
        </div>
      )}
    </div>
  );
};

export default RoutePlanningOSM;
