import React, { useState, useEffect } from 'react';
import EmotionInput from './components/EmotionInput';
import EnvironmentVisualizer from './components/EnvironmentVisualizer';
import AudioEngine from './components/AudioEngine';
import { websocketService } from './services/websocket';
import { apiService } from './services/api';
import './App.css';

function App() {
  const [emotion, setEmotion] = useState({
    joy: 0.5,
    calm: 0.5,
    energy: 0.5,
    melancholy: 0.5
  });

  const [isConnected, setIsConnected] = useState(false);
  const [emotionHistory, setEmotionHistory] = useState([]);

  // Initialize WebSocket connection
  useEffect(() => {
    websocketService.connect();
    const unsubscribe = websocketService.subscribe((data) => {
      if (data.type === 'emotion_update') {
        setEmotion(prevEmotion => ({
          ...prevEmotion,
          ...data.data
        }));
      }
    });

    // Load emotion history
    loadEmotionHistory();

    return () => {
      unsubscribe();
    };
  }, []);

  const loadEmotionHistory = async () => {
    try {
      const history = await apiService.getEmotionHistory();
      setEmotionHistory(history);
    } catch (error) {
      console.error('Error loading emotion history:', error);
    }
  };

  const handleEmotionChange = async (newEmotion) => {
    setEmotion(newEmotion);
    
    try {
      // Send to WebSocket for real-time updates
      websocketService.sendEmotion(newEmotion);
      
      // Save to backend
      const savedEmotion = await apiService.saveEmotion({
        ...newEmotion,
        timestamp: new Date().toISOString()
      });
      
      // Update history
      setEmotionHistory(prev => [savedEmotion, ...prev].slice(0, 10));
    } catch (error) {
      console.error('Error saving emotion:', error);
    }
  };

  return (
    <div className="app">
      <h1>Memory Weaver</h1>
      <EmotionInput 
        emotion={emotion} 
        onChange={handleEmotionChange}
        isConnected={isConnected}
      />
      <EnvironmentVisualizer emotion={emotion} />
      <AudioEngine emotion={emotion} />
      
      <div className="emotion-history">
        <h3>Recent Emotions</h3>
        <ul>
          {emotionHistory.map((entry, index) => (
            <li key={index}>
              <span>{new Date(entry.timestamp).toLocaleTimeString()}</span>
              <span>
                Joy: {Math.round(entry.joy * 100)}% | 
                Calm: {Math.round(entry.calm * 100)}% | 
                Energy: {Math.round(entry.energy * 100)}% | 
                Melancholy: {Math.round(entry.melancholy * 100)}%
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default App;
