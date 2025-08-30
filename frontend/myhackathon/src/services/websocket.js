// src/services/websocket.js
// WebSocket service for Django Channels

class WebSocketService {
  constructor() {
    this.ws = null;
    this.subscribers = [];
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 5000;
    this.offlineQueue = [];
  }

  connect() {
    if (this.isConnecting || this.ws?.readyState === WebSocket.OPEN) return;
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnection attempts reached. Please check your connection.');
      return;
    }

    this.isConnecting = true;

    try {
      this.ws = new WebSocket('ws://localhost:8000/ws/emotions/');
      
      this.ws.onopen = () => {
        console.log('Connected to WebSocket');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.processOfflineQueue();
        this.notifySubscribers({ type: 'connection_status', data: { isConnected: true } });
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.notifySubscribers(data);
      };

      this.ws.onclose = () => {
        console.log('Disconnected from WebSocket');
        this.isConnecting = false;
        this.notifySubscribers({ type: 'connection_status', data: { isConnected: false } });
        this.reconnectAttempts++;
        setTimeout(() => this.connect(), this.reconnectDelay);
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isConnecting = false;
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.isConnecting = false;
    }
  }

  subscribe(callback) {
    this.subscribers.push(callback);
    return () => {
      this.subscribers = this.subscribers.filter(cb => cb !== callback);
    };
  }

  notifySubscribers(data) {
    this.subscribers.forEach(callback => callback(data));
  }

  sendEmotion(emotionData) {
    const message = {
      type: 'emotion_update',
      data: emotionData,
      timestamp: new Date().toISOString()
    };

    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      // Store in offline queue
      this.offlineQueue.push(message);
      // Store in localStorage for persistence
      this.saveToLocalStorage(message);
    }
  }

  processOfflineQueue() {
    while (this.offlineQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
      const message = this.offlineQueue.shift();
      this.ws.send(JSON.stringify(message));
    }
  }

  saveToLocalStorage(message) {
    try {
      const offlineData = JSON.parse(localStorage.getItem('offlineEmotions') || '[]');
      offlineData.push(message);
      localStorage.setItem('offlineEmotions', JSON.stringify(offlineData.slice(-100))); // Keep last 100 items
    } catch (error) {
      console.error('Error saving to localStorage:', error);
    }
  }

  loadFromLocalStorage() {
    try {
      const offlineData = JSON.parse(localStorage.getItem('offlineEmotions') || '[]');
      this.offlineQueue = [...this.offlineQueue, ...offlineData];
      localStorage.removeItem('offlineEmotions');
    } catch (error) {
      console.error('Error loading from localStorage:', error);
    }
  }
}

// Create a singleton instance
const websocketService = new WebSocketService();
websocketService.loadFromLocalStorage(); // Load offline data on initialization

export { websocketService };
