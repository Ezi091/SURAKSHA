const API_BASE_URL = 'http://127.0.0.1:8000/api';

/**
 * Frontend service for calling SURAKSHA backend endpoints.
 *
 * Phase 2: Backend API is ready but frontend still uses mock data.
 * Phase 3+: Replace mock data with real API calls.
 * Phase 4: OSM routing API integrated.
 */

export const floodApi = {
  /**
   * POST /api/flood/predict
   * Run the flood prediction engine with given inputs.
   */
  async predict(request) {
    const response = await fetch(`${API_BASE_URL}/flood/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Prediction failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * GET /api/health
   * Check backend health.
   */
  async healthCheck() {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * POST /api/osm/safe-route
   * Calculate flood-safe routes using real OSM road data.
   */
  async calculateSafeRoute(request) {
    const response = await fetch(`${API_BASE_URL}/osm/safe-route`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Route calculation failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * GET /api/osm/landmarks
   * Get recognizable locations from OSM road names.
   */
  async getLandmarks() {
    const response = await fetch(`${API_BASE_URL}/osm/landmarks`);
    if (!response.ok) {
      throw new Error(`Failed to fetch landmarks: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * GET /api/osm/network-info
   * Get OSM road network statistics.
   */
  async getNetworkInfo() {
    const response = await fetch(`${API_BASE_URL}/osm/network-info`);
    if (!response.ok) {
      throw new Error(`Failed to fetch network info: ${response.statusText}`);
    }
    return response.json();
  },
};

