/**
 * Default synthetic inputs for Phase 3A
 * These provide sensible defaults so the backend can predict without external data
 *
 * Based on Phase 2 test scenarios
 */

export const DEFAULT_TERRAIN = {
  area_sqm: 10000.0,
  slope: 0.05,
  low_point_factor: 1.0,
  runoff_coefficient: 0.85
};

export const DEFAULT_DRAINAGE = {
  nodes: [
    { id: "drain_1", capacity_m3_hr: 150.0, blockage_factor: 0.15 },
    { id: "drain_2", capacity_m3_hr: 150.0, blockage_factor: 0.15 }
  ],
  edges: []
};

export const RAINFALL_PRESETS = {
  LIGHT: { intensity_mm_hr: 10.0, label: "Light Rain" },
  MODERATE: { intensity_mm_hr: 200.0, label: "Moderate Rain" },
  HEAVY: { intensity_mm_hr: 300.0, label: "Heavy Rain" },
  EXTREME: { intensity_mm_hr: 500.0, label: "Extreme Rain" }
};

/**
 * Build a flood forecast request for the backend
 * @param {number} rainfallIntensity - mm/hr
 * @param {number} horizons - how many time steps (1-4)
 * @returns {object} FloodForecastRequest ready for POST /api/flood/predict
 */
export function buildForecastRequest(rainfallIntensity, horizons = 4) {
  // Create forecasts for T+0 through T+N
  // For now, assume constant rainfall across horizons
  const forecasts = [];
  for (let i = 0; i < horizons; i++) {
    forecasts.push({
      horizon: `T+${i}`,
      rainfall: {
        intensity_mm_hr: rainfallIntensity,
        duration_hours: 1.0
      }
    });
  }

  return {
    terrain: DEFAULT_TERRAIN,
    drainage: DEFAULT_DRAINAGE,
    forecasts: forecasts
  };
}
