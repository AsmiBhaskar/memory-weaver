// src/services/api.js
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';
const OFFLINE_STORAGE_KEY = 'offlineEmotions';

const apiService = {
  isOnline: false,
  pendingRequests: new Map(),

  initializeOfflineSupport() {
    window.addEventListener('online', () => this.handleOnline());
    window.addEventListener('offline', () => this.handleOffline());
    this.isOnline = navigator.onLine;
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

      const response = await axios.post(`${API_BASE_URL}/emotions/`, emotionData);
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

      const syncPromises = offlineData.map(data => 
        axios.post(`${API_BASE_URL}/emotions/`, data)
          .then(response => ({ success: true, data: response.data, originalData: data }))
          .catch(error => ({ success: false, error, originalData: data }))
      );

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

      const response = await axios.get(`${API_BASE_URL}/emotions/`);
      return response.data;
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

  async analyzeImage(imageData) {
    if (!this.isOnline) {
      console.log('Image analysis not available offline');
      return null;
    }

    try {
      const response = await axios.post(`${API_BASE_URL}/analyze-image/`, {
        image: imageData
      });
      return response.data;
    } catch (error) {
      console.error('Error analyzing image:', error);
      throw error;
    }
  },

  async analyzeVoice(audioData) {
    if (!this.isOnline) {
      console.log('Voice analysis not available offline');
      return null;
    }

    try {
      const response = await axios.post(`${API_BASE_URL}/analyze-voice/`, {
        audio: audioData
      });
      return response.data;
    } catch (error) {
      console.error('Error analyzing voice:', error);
      throw error;
    }
  }
};

// Initialize offline support
apiService.initializeOfflineSupport();

export { apiService };
