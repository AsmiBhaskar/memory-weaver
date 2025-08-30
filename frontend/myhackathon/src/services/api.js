// src/services/api.js
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/emotions/api';
const OFFLINE_STORAGE_KEY = 'offlineEmotions';

const apiService = {
  isOnline: false,
  pendingRequests: new Map(),
  sessionId: null,

  initializeOfflineSupport() {
    window.addEventListener('online', () => this.handleOnline());
    window.addEventListener('offline', () => this.handleOffline());
    this.isOnline = navigator.onLine;
    
    // Get or create session ID
    this.sessionId = this.getOrCreateSessionId();
  },

  getOrCreateSessionId() {
    let sessionId = localStorage.getItem('emotion_session_id');
    if (!sessionId) {
      sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('emotion_session_id', sessionId);
    }
    return sessionId;
  },

  handleOffline() {
    this.isOnline = false;
    console.log('Application is offline. Data will be saved locally.');
  },

  async handleOnline() {
    this.isOnline = true;
    console.log('Application is online. Syncing data...');
    await this.syncOfflineData();
  },

  async saveEmotion(emotionData) {
    try {
      if (!this.isOnline) {
        return this.saveOffline(emotionData);
      }

      const dataToSend = {
        session_id: this.sessionId,
        joy: emotionData.joy || 0,
        sadness: Math.max(0, 1 - (emotionData.calm || 0)),  // Inverse of calm
        anger: 0,
        fear: 0,
        surprise: emotionData.energy * 0.3 || 0,  // Map energy to surprise
        disgust: 0,
        valence: (emotionData.joy + emotionData.calm - emotionData.melancholy) / 3,
        arousal: emotionData.energy || 0,
        environment_data: {
          lighting: "normal",
          noise_level: "normal", 
          temperature: 20,
          social_context: "individual"
        }
      };

      const response = await axios.post(`${API_BASE_URL}/readings/`, dataToSend);
      return response.data;
    } catch (error) {
      console.error('Error saving emotion:', error);
      if (axios.isAxiosError(error) && !error.response) {
        // Network error - save offline
        return this.saveOffline(emotionData);
      }
      throw error;
    }
  },

  saveOffline(emotionData) {
    try {
      const offlineData = JSON.parse(localStorage.getItem(OFFLINE_STORAGE_KEY) || '[]');
      const dataWithTimestamp = {
        ...emotionData,
        session_id: this.sessionId,
        timestamp: new Date().toISOString(),
        id: `offline_${Date.now()}`
      };
      offlineData.push(dataWithTimestamp);
      localStorage.setItem(OFFLINE_STORAGE_KEY, JSON.stringify(offlineData));
      return dataWithTimestamp;
    } catch (error) {
      console.error('Error saving offline:', error);
      throw error;
    }
  },

  async syncOfflineData() {
    try {
      const offlineData = JSON.parse(localStorage.getItem(OFFLINE_STORAGE_KEY) || '[]');
      if (offlineData.length === 0) return;

      const syncPromises = offlineData.map(data => {
        const dataToSend = {
          session_id: data.session_id || this.sessionId,
          joy: data.joy || 0,
          sadness: Math.max(0, 1 - (data.calm || 0)),
          anger: 0,
          fear: 0,
          surprise: data.energy * 0.3 || 0,
          disgust: 0,
          valence: (data.joy + (data.calm || 0) - (data.melancholy || 0)) / 3,
          arousal: data.energy || 0,
          environment_data: {
            lighting: "normal",
            noise_level: "normal",
            temperature: 20,
            social_context: "individual"
          }
        };
        
        return axios.post(`${API_BASE_URL}/readings/`, dataToSend)
          .then(response => ({ success: true, data: response.data, originalData: data }))
          .catch(error => ({ success: false, error, originalData: data }));
      });

      const results = await Promise.all(syncPromises);
      
      // Keep failed items in offline storage
      const failedItems = results
        .filter(result => !result.success)
        .map(result => result.originalData);

      localStorage.setItem(OFFLINE_STORAGE_KEY, JSON.stringify(failedItems));
      
      return results;
    } catch (error) {
      console.error('Error syncing offline data:', error);
      throw error;
    }
  },

  async getEmotionHistory() {
    try {
      if (!this.isOnline) {
        return this.getOfflineHistory();
      }

      const response = await axios.get(`${API_BASE_URL}/readings/`);
      return response.data.results || response.data;
    } catch (error) {
      console.error('Error fetching emotion history:', error);
      if (axios.isAxiosError(error) && !error.response) {
        return this.getOfflineHistory();
      }
      throw error;
    }
  },

  getOfflineHistory() {
    try {
      return JSON.parse(localStorage.getItem(OFFLINE_STORAGE_KEY) || '[]');
    } catch (error) {
      console.error('Error getting offline history:', error);
      return [];
    }
  },

  async getCollectiveEmotions() {
    try {
      if (!this.isOnline) {
        console.log('Collective emotions not available offline');
        return null;
      }

      const response = await axios.get(`${API_BASE_URL}/collective/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching collective emotions:', error);
      return null;
    }
  },

  async getSystemHealth() {
    try {
      if (!this.isOnline) {
        return { status: 'offline' };
      }

      const response = await axios.get(`${API_BASE_URL}/system/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching system health:', error);
      return { status: 'error', error: error.message };
    }
  }
};

// Initialize offline support
apiService.initializeOfflineSupport();

export { apiService };
