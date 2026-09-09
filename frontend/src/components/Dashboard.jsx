import React, { useState, useEffect } from 'react';
import Header from './Header';
import MetricsCards from './MetricsCards';
import FloodMapOSM from './FloodMapOSM';
import Timeline from './Timeline';
import RainfallSimulation from './RainfallSimulation';
import RoutePlanningOSM from './RoutePlanningOSM';
import RouteResultsOSM from './RouteResultsOSM';
import { floodApi } from '../services/floodApi';
import { buildForecastRequest, RAINFALL_PRESETS } from '../data/defaultInputs';
import './Dashboard.css';

const Dashboard = () => {
  const [timeIndex, setTimeIndex] = useState(0);
  const [rainfallIntensity, setRainfallIntensity] = useState(RAINFALL_PRESETS.MODERATE.intensity_mm_hr);
  const [predictions, setPredictions] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [backendHealthy, setBackendHealthy] = useState(null);
  const [routeResult, setRouteResult] = useState(null);
  const [routeLoading, setRouteLoading] = useState(false);
  const [routeError, setRouteError] = useState(null);

  // Check backend health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await floodApi.healthCheck();
        setBackendHealthy(true);
      } catch (err) {
        setBackendHealthy(false);
        setError('Backend is unavailable. Make sure FastAPI is running on localhost:8001');
      }
    };
    checkHealth();
  }, []);

  // Fetch predictions when rainfall changes
  const handleRainfallChange = async (intensity) => {
    setRainfallIntensity(intensity);
    setIsLoading(true);
    setError(null);
    setTimeIndex(0); // Reset to T+0

    try {
      const request = buildForecastRequest(intensity, 4);
      const response = await floodApi.predict(request);
      setPredictions(response.predictions);
      setBackendHealthy(true);
    } catch (err) {
      setError(`Prediction failed: ${err.message}`);
      setPredictions(null);
      setBackendHealthy(false);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle route calculation
  const handleRouteCalculated = (result) => {
    setRouteResult(result);
    setRouteError(result.error || null);
  };

  // Initial load with default rainfall
  useEffect(() => {
    if (backendHealthy === true) {
      handleRainfallChange(rainfallIntensity);
    }
  }, [backendHealthy]);

  // Build current display data from predictions
  const getCurrentData = () => {
    if (!predictions || predictions.length === 0) {
      return {
        metrics: {
          rainfall: 'N/A',
          drainage: 'N/A',
          maxDepth: 'N/A',
          highRiskLocations: 0,
          systemStatus: 'Unknown'
        },
        zones: [],
        mapCenter: [19.0760, 72.8777]
      };
    }

    const prediction = predictions[timeIndex];

    // Determine system status based on risk level and utilization
    let systemStatus = 'Normal';
    if (prediction.flood_risk === 'SEVERE') systemStatus = 'Evacuation';
    else if (prediction.flood_risk === 'HIGH') systemStatus = 'Critical';
    else if (prediction.flood_risk === 'MODERATE') systemStatus = 'Warning';
    else systemStatus = 'Safe';

    // Generate demo zones based on water depth and risk level
    const zoneRisk = prediction.flood_risk.toLowerCase();
    const depth = prediction.predicted_water_depth_cm;

    // Create demo zones with risk levels
    const baseZones = [
      { id: 1, coordinates: [19.080, 72.880], radius: 600 },
      { id: 2, coordinates: [19.065, 72.870], radius: 400 },
      { id: 3, coordinates: [19.090, 72.865], radius: 800 },
      { id: 4, coordinates: [19.072, 72.890], radius: 500 },
      { id: 5, coordinates: [19.055, 72.885], radius: 700 }
    ];

    // Adjust zone sizes and risks based on predicted depth
    const zones = baseZones.map(zone => ({
      ...zone,
      radius: Math.round(zone.radius * (1 + depth / 100)), // Scale radius with depth
      risk: zoneRisk
    }));

    // Count high-risk locations (zones with HIGH or SEVERE risk)
    const highRiskLocations = zoneRisk === 'high' || zoneRisk === 'severe' ? zones.length : 0;

    return {
      metrics: {
        rainfall: `${prediction.rainfall_intensity.toFixed(1)} mm/hr`,
        drainage: `${prediction.drainage_utilization_pct.toFixed(1)}%`,
        maxDepth: `${prediction.predicted_water_depth_cm.toFixed(1)} cm`,
        highRiskLocations: highRiskLocations,
        systemStatus: systemStatus
      },
      zones: zones,
      mapCenter: [19.0760, 72.8777]
    };
  };

  const currentData = getCurrentData();

  return (
    <div className="dashboard-layout">
      <Header systemStatus={currentData.metrics.systemStatus} />

      {error && (
        <div className="error-banner">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      <main className="dashboard-content">
        <div className="dashboard-sidebar">
          <RainfallSimulation
            currentRainfall={rainfallIntensity}
            onRainfallChange={handleRainfallChange}
            isLoading={isLoading}
          />

          <MetricsCards metrics={currentData.metrics} />
          <Timeline timeIndex={timeIndex} setTimeIndex={setTimeIndex} totalHorizons={predictions?.length || 0} />

          <RoutePlanningOSM
            onRouteCalculated={handleRouteCalculated}
            isLoading={routeLoading}
            error={routeError}
            currentPrediction={predictions && predictions.length > 0 ? predictions[timeIndex] : null}
            predictions={predictions}
          />
        </div>

        <div className="dashboard-main-area">
          <FloodMapOSM center={currentData.mapCenter} zones={currentData.zones} route={routeResult} />
        </div>
      </main>

      {routeResult && (
        <div className="dashboard-route-panel">
          <RouteResultsOSM route={routeResult} isLoading={routeLoading} />
        </div>
      )}
    </div>
  );
};

export default Dashboard;