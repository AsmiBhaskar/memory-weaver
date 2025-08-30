// src/components/EnvironmentVisualizer.js
import React from 'react';

const EnvironmentVisualizer = ({ emotion }) => {
  // Simple color logic based on dominant emotion
  const getColor = () => {
    const { joy, calm, energy, melancholy } = emotion;
    if (joy > 0.6) return '#FFD700';
    if (calm > 0.6) return '#4FC3F7';
    if (energy > 0.6) return '#FF6B35';
    if (melancholy > 0.6) return '#9C27B0';
    return '#CCCCCC';
  };

  return (
    <div className="environment-visualizer" style={{ background: getColor(), height: '200px', borderRadius: '10px', margin: '20px 0' }}>
      <h4>Environment Visualizer</h4>
      <p>Color changes with emotion!</p>
    </div>
  );
};

export default EnvironmentVisualizer;
