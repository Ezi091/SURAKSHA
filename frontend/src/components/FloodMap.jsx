import React from 'react';
import { MapContainer, TileLayer, Circle, Popup, Polyline, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './FloodMap.css';

// Node mapping for demo network
const NODE_COORDS = {
  n1: [19.080, 72.860], // Downtown
  n2: [19.085, 72.880], // Hospital
  n3: [19.060, 72.860], // Airport
  n4: [19.070, 72.890], // Port
  n5: [19.050, 72.880], // Suburbs
};

// Segment definitions
const SEGMENT_DEFS = {
  s1: { start: 'n1', end: 'n2' },
  s2: { start: 'n1', end: 'n3' },
  s3: { start: 'n2', end: 'n4' },
  s4: { start: 'n3', end: 'n4' },
  s5: { start: 'n3', end: 'n5' },
  s6: { start: 'n4', end: 'n5' },
};

const Legend = () => (
  <div className="map-legend">
    <div className="legend-header">
      <h4>Flood Risk Legend</h4>
    </div>

    <div className="legend-section">
      <div className="legend-section-title">Water Depth & Risk</div>

      <div className="legend-item">
        <div className="legend-circle high"></div>
        <div className="legend-item-content">
          <div className="legend-label">Severe Risk</div>
          <div className="legend-value">&gt; 50 cm</div>
        </div>
      </div>

      <div className="legend-item">
        <div className="legend-circle high-mod"></div>
        <div className="legend-item-content">
          <div className="legend-label">High Risk</div>
          <div className="legend-value">30–50 cm</div>
        </div>
      </div>

      <div className="legend-item">
        <div className="legend-circle moderate"></div>
        <div className="legend-item-content">
          <div className="legend-label">Moderate Risk</div>
          <div className="legend-value">15–30 cm</div>
        </div>
      </div>

      <div className="legend-item">
        <div className="legend-circle low"></div>
        <div className="legend-item-content">
          <div className="legend-label">Low Risk</div>
          <div className="legend-value">&lt; 15 cm</div>
        </div>
      </div>
    </div>

    <div className="legend-divider"></div>

    <div className="legend-section">
      <div className="legend-section-title">Routes</div>
      <div className="legend-info-item">
        <span className="route-line safe">━</span>
        <span className="info-text">Safe Recommended Route</span>
      </div>
      <div className="legend-info-item">
        <span className="route-line avoided">━</span>
        <span className="info-text">Flooded (Avoided)</span>
      </div>
      <div className="legend-info-item">
        <span className="route-line normal">╍</span>
        <span className="info-text">Normal Route</span>
      </div>
    </div>

    <div className="legend-divider"></div>

    <div className="legend-section">
      <div className="legend-section-title">Map Information</div>
      <div className="legend-info-item">
        <span className="info-icon">●</span>
        <span className="info-text">Zones show predicted flood areas</span>
      </div>
      <div className="legend-info-item">
        <span className="info-icon">↻</span>
        <span className="info-text">Click zones for details</span>
      </div>
    </div>

    <div className="legend-footer">
      <small>Data from SURAKSHA Physics Model</small>
    </div>
  </div>
);

// MapUpdater component to smoothly handle center/zoom changes if needed later
const MapUpdater = ({ center }) => {
  const map = useMap();
  map.setView(center, map.getZoom());
  return null;
};

const FloodMap = ({ center, zones, route }) => {
  const getRiskColor = (risk) => {
    switch(risk) {
      case 'high': return '#ef4444'; // Red
      case 'moderate': return '#f59e0b'; // Amber
      case 'low': return '#3b82f6'; // Blue
      default: return '#3b82f6';
    }
  };

  const getRiskFillOpacity = (risk) => {
    switch(risk) {
      case 'high': return 0.5;
      case 'moderate': return 0.4;
      case 'low': return 0.3;
      default: return 0.3;
    }
  };

  const renderRoutes = () => {
    if (!route || route.error) return null;

    const { normal_route, safe_route, avoided_segments } = route;

    // We will render elements in a specific order so safe route appears on top

    // 1. Draw normal route segments (that are not part of safe route)
    const normalPolys = normal_route.segment_ids.map(segId => {
      const def = SEGMENT_DEFS[segId];
      if (!def) return null;
      const positions = [NODE_COORDS[def.start], NODE_COORDS[def.end]];
      const isAvoided = avoided_segments.includes(segId);

      // If it's part of the safe route too, we'll draw it in the safe route map to avoid overlap issues
      if (safe_route.segment_ids.includes(segId)) return null;

      return (
        <Polyline
          key={`normal-${segId}`}
          positions={positions}
          color={isAvoided ? "#ef4444" : "#9ca3af"} // Red if avoided, gray if normal
          weight={isAvoided ? 6 : 4}
          dashArray={isAvoided ? undefined : "5, 10"}
          opacity={0.8}
        >
          <Popup>
            <strong>Route Segment: {segId}</strong><br />
            Type: {isAvoided ? "Flooded / High Risk (Avoided)" : "Normal Route"}<br/>
            From: {def.start} To: {def.end}
          </Popup>
        </Polyline>
      );
    });

    // 2. Draw safe route segments
    const safePolys = safe_route.segment_ids.map(segId => {
      const def = SEGMENT_DEFS[segId];
      if (!def) return null;
      const positions = [NODE_COORDS[def.start], NODE_COORDS[def.end]];

      return (
        <Polyline
          key={`safe-${segId}`}
          positions={positions}
          color="#10b981" // Emerald green
          weight={6}
          opacity={0.9}
        >
          <Popup>
            <strong>Route Segment: {segId}</strong><br />
            Type: Safe Recommended Route<br/>
            From: {def.start} To: {def.end}
          </Popup>
        </Polyline>
      );
    });

    return [...normalPolys.filter(Boolean), ...safePolys.filter(Boolean)];
  };

  return (
    <div className="map-wrapper">
      <MapContainer
        center={center}
        zoom={12}
        scrollWheelZoom={true}
        className="flood-map"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {zones.map(zone => (
          <Circle
            key={zone.id}
            center={zone.coordinates}
            radius={zone.radius}
            pathOptions={{
              color: getRiskColor(zone.risk),
              fillColor: getRiskColor(zone.risk),
              fillOpacity: getRiskFillOpacity(zone.risk),
              weight: 2
            }}
          >
            <Popup>
              <strong>Zone {zone.id}</strong><br/>
              Risk Level: {zone.risk.toUpperCase()}<br/>
              Est. Radius: {zone.radius}m
            </Popup>
          </Circle>
        ))}

        {renderRoutes()}

        {/* Force map view update if center changes */}
        <MapUpdater center={center} />
      </MapContainer>

      <Legend />
    </div>
  );
};

export default FloodMap;