import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Circle, Popup, Polyline, Marker, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './FloodMapOSM.css';

// Create custom panes with correct z-index layering
const PaneSetup = () => {
  const map = useMap();
  useEffect(() => {
    if (map) {
      // Route highlighting pane (above OSM roads)
      if (!map.getPane('routeHighlight')) {
        const pane = map.createPane('routeHighlight');
        pane.style.zIndex = 450;
      }
      // Route inner line pane (above highlighting)
      if (!map.getPane('routeLine')) {
        const pane = map.createPane('routeLine');
        pane.style.zIndex = 460;
      }
      // Location labels pane (above everything)
      if (!map.getPane('locationLabels')) {
        const pane = map.createPane('locationLabels');
        pane.style.zIndex = 700;
      }
    }
  }, [map]);
  return null;
};

// Custom location label component
const LocationLabel = ({ position, name, type }) => {
  const map = useMap();

  useEffect(() => {
    if (!map || !position || !name || !type) return;

    try {
      const icon = L.divIcon({
        html: `<div class="location-label ${type || ''}">
          <div class="location-label-pin">📍</div>
          <div class="location-label-text">${name || ''}</div>
          <div class="location-label-type">${type ? type.toUpperCase() : 'LOCATION'}</div>
        </div>`,
        className: 'location-label-icon',
        iconSize: [160, 60],
        iconAnchor: [80, 30],
        popupAnchor: [0, 0]
      });

      const marker = L.marker(position, {
        icon: icon,
        pane: 'locationLabels',
        interactive: false
      }).addTo(map);

      return () => {
        if (map && marker) {
          try { map.removeLayer(marker); } catch (e) { /* ignore */ }
        }
      };
    } catch (e) {
      console.warn('Failed to create location label:', e);
    }
  }, [map, position, name, type]);

  return null;
};

const Legend = () => (
  <div className="map-legend">
    <div className="legend-header">
      <h4>Map Legend</h4>
    </div>

    <div className="legend-section">
      <div className="legend-section-title">Flood Risk Zones</div>

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
      <div className="legend-section-title">Route Safety</div>

      <div className="legend-info-item">
        <span className="route-line safe">━</span>
        <span className="info-text">Safe Route (Green)</span>
      </div>

      <div className="legend-info-item">
        <span className="route-line avoided">━</span>
        <span className="info-text">Flooded/High-Risk (Red)</span>
      </div>

      <div className="legend-info-item">
        <span className="route-line normal">╍</span>
        <span className="info-text">Normal Route Context</span>
      </div>
    </div>

    <div className="legend-divider"></div>

    <div className="legend-section">
      <div className="legend-section-title">Locations</div>
      <div className="legend-info-item">
        <span className="marker-icon origin">📍</span>
        <span className="info-text">Origin</span>
      </div>
      <div className="legend-info-item">
        <span className="marker-icon destination">📍</span>
        <span className="info-text">Destination</span>
      </div>
    </div>

    <div className="legend-footer">
      <small>OSM Roads + SURAKSHA Flood Prediction</small>
    </div>
  </div>
);

const MapUpdater = ({ center, zoom }) => {
  const map = useMap();
  useEffect(() => {
    if (center && zoom) {
      map.setView(center, zoom);
    } else if (center) {
      map.setView(center, map.getZoom());
    }
  }, [center, zoom, map]);
  return null;
};

// Render route with outer casing and inner colored line
const RouteLayer = ({ route }) => {
  const map = useMap();

  useEffect(() => {
    if (!map || !route || route.error || !route.normal_route) return;

    const layers = [];
    const isSafe = !route.needs_rerouting;

    try {
      const { normal_route, safe_route, avoided_segments } = route;
      const avoidedSet = new Set(avoided_segments || []);
      const safeSet = new Set((safe_route?.segment_ids) || []);

      // Helper to create polyline with proper pane
      const createCasingLine = (positions, key) => {
        const line = L.polyline(positions, {
          color: 'white',
          weight: 16,
          opacity: 0.95,
          lineCap: 'round',
          lineJoin: 'round',
          pane: 'routeHighlight'
        });
        line._key = key;
        return line;
      };

      const createRouteLine = (positions, color, key) => {
        const line = L.polyline(positions, {
          color: color,
          weight: 10,
          opacity: 1,
          lineCap: 'round',
          lineJoin: 'round',
          pane: 'routeLine'
        });
        line.bringToFront();
        line._key = key;
        return line;
      };

      if (isSafe) {
        // SAFE: Show normal route in THICK GREEN
        if (normal_route?.geometry) {
          normal_route.geometry.forEach((geom, idx) => {
            if (geom && geom.length >= 2) {
              const positions = geom.map(([lon, lat]) => [lat, lon]);
              layers.push(createCasingLine(positions, `casing-safe-${idx}`));
              layers.push(createRouteLine(positions, '#10b981', `line-safe-${idx}`));
            }
          });
        }
      } else {
        // UNSAFE: Show RED original + GREEN safe alternative

        // Render RED avoided segments (original unsafe)
        if (normal_route?.geometry && avoided_segments?.length > 0) {
          normal_route.geometry.forEach((geom, idx) => {
            const segId = normal_route.segment_ids[idx];
            if (avoidedSet.has(segId) && geom && geom.length >= 2) {
              const positions = geom.map(([lon, lat]) => [lat, lon]);
              layers.push(createCasingLine(positions, `casing-red-${idx}`));
              layers.push(createRouteLine(positions, '#ef4444', `line-red-${idx}`));
            }
          });
        }

        // Render GREEN safe route (rendered last = on top)
        if (safe_route?.geometry) {
          safe_route.geometry.forEach((geom, idx) => {
            if (geom && geom.length >= 2) {
              const positions = geom.map(([lon, lat]) => [lat, lon]);
              layers.push(createCasingLine(positions, `casing-green-${idx}`));
              layers.push(createRouteLine(positions, '#10b981', `line-green-${idx}`));
            }
          });
        }
      }

      // Add all layers to map
      layers.forEach(layer => map.addLayer(layer));

      return () => {
        layers.forEach(layer => map.removeLayer(layer));
      };
    } catch (err) {
      console.error('Route rendering error:', err);
    }
  }, [map, route]);

  return null;
};

const FloodMapOSM = ({ center, zones, route }) => {
  const getRiskColor = (risk) => {
    const riskLower = risk?.toLowerCase() || 'low';
    switch(riskLower) {
      case 'severe': return '#ef4444';
      case 'high': return '#f97316';
      case 'moderate': return '#f59e0b';
      case 'low': return '#3b82f6';
      default: return '#3b82f6';
    }
  };

  const getRiskFillOpacity = (risk) => {
    const riskLower = risk?.toLowerCase() || 'low';
    switch(riskLower) {
      case 'severe': return 0.6;
      case 'high': return 0.5;
      case 'moderate': return 0.4;
      case 'low': return 0.2;
      default: return 0.2;
    }
  };

  return (
    <div className="map-wrapper">
      <MapContainer
        center={center || [19.0760, 72.8777]}
        zoom={13}
        scrollWheelZoom={true}
        className="flood-map"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Setup custom panes for layering */}
        <PaneSetup />

        {/* Flood risk zones */}
        {zones && zones.map(zone => (
          <Circle
            key={zone.id}
            center={zone.coordinates}
            radius={zone.radius}
            pathOptions={{
              color: getRiskColor(zone.risk),
              fillColor: getRiskColor(zone.risk),
              fillOpacity: getRiskFillOpacity(zone.risk),
              weight: 1.5
            }}
          >
            <Popup>
              <strong>Flood Zone {zone.id}</strong><br/>
              Risk Level: {zone.risk?.toUpperCase()}<br/>
              Est. Radius: {zone.radius.toLocaleString()}m
            </Popup>
          </Circle>
        ))}

        {/* Route rendering with proper layering */}
        <RouteLayer route={route} />

        {/* Origin and destination location labels */}
        {route && route.normal_route?.origin_coords && (
          <LocationLabel
            position={[route.normal_route.origin_coords[0], route.normal_route.origin_coords[1]]}
            name={route.normal_route.origin || 'Origin'}
            type="origin"
          />
        )}
        {route && route.normal_route?.destination_coords && (
          <LocationLabel
            position={[route.normal_route.destination_coords[0], route.normal_route.destination_coords[1]]}
            name={route.normal_route.destination || 'Destination'}
            type="destination"
          />
        )}

        {/* Map updater for center/zoom changes */}
        <MapUpdater center={center} />
      </MapContainer>

      <Legend />
    </div>
  );
};

export default FloodMapOSM;
