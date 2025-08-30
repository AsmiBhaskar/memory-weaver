// src/services/websocket.js
// WebSocket service for Django Channels

class WebSocketService {
  constructor() {
    this.socket = null;
    this.callbacks = {};
  }

  connect() {
    // Connect to Django Channels WebSocket
    this.socket = new WebSocket('ws://localhost:8000/ws/emotions/');
    this.socket.onopen = () => {
      console.log('Connected to real-time updates');
    };
    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (this.callbacks[data.type]) {
        this.callbacks[data.type](data.data);
      }
    };
    this.socket.onclose = () => {
      console.log('WebSocket connection closed');
    };
    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  subscribe(eventType, callback) {
    this.callbacks[eventType] = callback;
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}

export default new WebSocketService();
