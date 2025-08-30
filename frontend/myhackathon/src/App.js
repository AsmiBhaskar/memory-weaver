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

  // Initialize WebSocket connection and handle online/offline states
  useEffect(() => {
    websocketService.connect();
    const unsubscribe = websocketService.subscribe((data) => {
      if (data.type === 'emotion_update') {
        setEmotion(prevEmotion => ({
          ...prevEmotion,
          ...data.data
        }));
      } else if (data.type === 'connection_status') {
        setIsConnected(data.data.isConnected);
      }
    });

    // Load emotion history
    loadEmotionHistory();

    // Handle online/offline status
    const handleOnline = () => {
      console.log('App is online');
      setIsConnected(true);
      loadEmotionHistory(); // Reload history when coming back online
    };

    const handleOffline = () => {
      console.log('App is offline');
      setIsConnected(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    // Set initial online status
    setIsConnected(navigator.onLine);

    return () => {
      unsubscribe();
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
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
