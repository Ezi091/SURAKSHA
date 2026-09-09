export const getMockData = (timeIndex) => {
  // timeIndex maps to T+0, T+1, T+2, T+3

  // Center: Mumbai
  const MAP_CENTER = [19.0760, 72.8777];

  const dataSets = {
    0: {
      metrics: {
        rainfall: "68 mm/hr",
        drainage: "117%",
        maxDepth: "24 cm",
        highRiskLocations: 3,
        systemStatus: "Warning"
      },
      zones: [
        { id: 1, coordinates: [19.080, 72.880], radius: 600, risk: "moderate" },
        { id: 2, coordinates: [19.065, 72.870], radius: 400, risk: "low" },
        { id: 3, coordinates: [19.090, 72.865], radius: 800, risk: "high" },
        { id: 4, coordinates: [19.072, 72.890], radius: 500, risk: "high" },
        { id: 5, coordinates: [19.055, 72.885], radius: 700, risk: "high" }
      ]
    },
    1: {
      metrics: {
        rainfall: "75 mm/hr",
        drainage: "135%",
        maxDepth: "38 cm",
        highRiskLocations: 5,
        systemStatus: "Critical"
      },
      zones: [
        { id: 1, coordinates: [19.080, 72.880], radius: 800, risk: "high" },
        { id: 2, coordinates: [19.065, 72.870], radius: 600, risk: "moderate" },
        { id: 3, coordinates: [19.090, 72.865], radius: 1000, risk: "high" },
        { id: 4, coordinates: [19.072, 72.890], radius: 700, risk: "high" },
        { id: 5, coordinates: [19.055, 72.885], radius: 850, risk: "high" },
        { id: 6, coordinates: [19.085, 72.855], radius: 500, risk: "moderate" },
        { id: 7, coordinates: [19.060, 72.895], radius: 450, risk: "high" }
      ]
    },
    2: {
      metrics: {
        rainfall: "92 mm/hr",
        drainage: "160%",
        maxDepth: "56 cm",
        highRiskLocations: 8,
        systemStatus: "Severe"
      },
      zones: [
        { id: 1, coordinates: [19.080, 72.880], radius: 1100, risk: "high" },
        { id: 2, coordinates: [19.065, 72.870], radius: 900, risk: "high" },
        { id: 3, coordinates: [19.090, 72.865], radius: 1300, risk: "high" },
        { id: 4, coordinates: [19.072, 72.890], radius: 950, risk: "high" },
        { id: 5, coordinates: [19.055, 72.885], radius: 1100, risk: "high" },
        { id: 6, coordinates: [19.085, 72.855], radius: 750, risk: "high" },
        { id: 7, coordinates: [19.060, 72.895], radius: 800, risk: "high" },
        { id: 8, coordinates: [19.095, 72.895], radius: 600, risk: "moderate" }
      ]
    },
    3: {
      metrics: {
        rainfall: "105 mm/hr",
        drainage: "185%",
        maxDepth: "82 cm",
        highRiskLocations: 12,
        systemStatus: "Evacuation"
      },
      zones: [
        { id: 1, coordinates: [19.080, 72.880], radius: 1500, risk: "high" },
        { id: 2, coordinates: [19.065, 72.870], radius: 1200, risk: "high" },
        { id: 3, coordinates: [19.090, 72.865], radius: 1800, risk: "high" },
        { id: 4, coordinates: [19.072, 72.890], radius: 1400, risk: "high" },
        { id: 5, coordinates: [19.055, 72.885], radius: 1600, risk: "high" },
        { id: 6, coordinates: [19.085, 72.855], radius: 1200, risk: "high" },
        { id: 7, coordinates: [19.060, 72.895], radius: 1350, risk: "high" },
        { id: 8, coordinates: [19.095, 72.895], radius: 1000, risk: "high" },
        { id: 9, coordinates: [19.045, 72.875], radius: 900, risk: "high" },
        { id: 10, coordinates: [19.065, 72.850], radius: 850, risk: "high" },
        { id: 11, coordinates: [19.050, 72.860], radius: 700, risk: "moderate" },
        { id: 12, coordinates: [19.100, 72.875], radius: 950, risk: "high" }
      ]
    }
  };

  return {
    mapCenter: MAP_CENTER,
    ...dataSets[timeIndex]
  };
};