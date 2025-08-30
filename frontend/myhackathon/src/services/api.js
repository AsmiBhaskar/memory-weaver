// src/services/api.js
import axios from 'axios';

export const emotionAPI = {
  submitEmotion: async (emotionData) => {
    const response = await axios.post('http://localhost:8000/api/emotions/', emotionData);
    return response.data;
  },

  getEmotionHistory: async (sessionId) => {
    const response = await axios.get('http://localhost:8000/api/emotions/history/', {
      params: { session_id: sessionId }
    });
    return response.data;
  }
};
