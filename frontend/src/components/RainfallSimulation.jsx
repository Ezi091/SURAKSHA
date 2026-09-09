import React, { useState } from 'react';
import { RAINFALL_PRESETS } from '../data/defaultInputs';
import './RainfallSimulation.css';

const RainfallSimulation = ({ currentRainfall, onRainfallChange, isLoading }) => {
  const [customRainfall, setCustomRainfall] = useState(currentRainfall);

  const handlePresetClick = (intensity) => {
    setCustomRainfall(intensity);
    onRainfallChange(intensity);
  };

  const handleCustomChange = (e) => {
    const value = parseFloat(e.target.value) || 0;
    setCustomRainfall(value);
  };

  const handleCustomSubmit = () => {
    onRainfallChange(customRainfall);
  };

  return (
    <div className="rainfall-simulation">
      <h3>Rainfall Simulation</h3>

      <div className="rainfall-display">
        <div className="rainfall-value">
          <span className="label">Current Intensity:</span>
          <span className="value">{currentRainfall.toFixed(1)} mm/hr</span>
        </div>
      </div>

      <div className="preset-buttons">
        <p className="preset-label">Quick Presets:</p>
        <div className="button-group">
          {Object.entries(RAINFALL_PRESETS).map(([key, preset]) => (
            <button
              key={key}
              className={`preset-btn ${currentRainfall === preset.intensity_mm_hr ? 'active' : ''}`}
              onClick={() => handlePresetClick(preset.intensity_mm_hr)}
              disabled={isLoading}
              title={preset.label}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      <div className="custom-rainfall">
        <p className="custom-label">Custom Rainfall (mm/hr):</p>
        <div className="input-group">
          <input
            type="number"
            min="0"
            max="300"
            step="5"
            value={customRainfall}
            onChange={handleCustomChange}
            disabled={isLoading}
            placeholder="Enter rainfall intensity"
          />
          <button
            className="apply-btn"
            onClick={handleCustomSubmit}
            disabled={isLoading}
          >
            {isLoading ? 'Predicting...' : 'Apply'}
          </button>
        </div>
      </div>

      {isLoading && (
        <div className="loading-indicator">
          <div className="spinner"></div>
          <span>Running flood prediction...</span>
        </div>
      )}
    </div>
  );
};

export default RainfallSimulation;
