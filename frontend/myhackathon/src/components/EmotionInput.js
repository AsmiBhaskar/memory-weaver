// src/components/EmotionInput.js
import React, { useState, useRef, useEffect } from 'react';

const EmotionInput = ({ emotion, onChange, isConnected }) => {
  const [inputMethod, setInputMethod] = useState('manual'); // 'manual', 'webcam', 'voice'
  const [isProcessing, setIsProcessing] = useState(false);
  const [cameraStream, setCameraStream] = useState(null);
  const [voiceRecognition, setVoiceRecognition] = useState(null);
  const videoRef = useRef(null);
  
  useEffect(() => {
    return () => {
      stopWebcam();
      stopVoice();
    };
  }, []);

  // Manual Sliders
  const handleSliderChange = (emotionType, value) => {
    onChange({
      ...emotion,
      [emotionType]: value
    });
  };

  // Webcam Input
  const startWebcam = async () => {
    try {
      setIsProcessing(true);
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: "user" } 
      });
      
      videoRef.current.srcObject = stream;
      setCameraStream(stream);
      setInputMethod('webcam');
      startEmotionDetection();
    } catch (error) {
      console.error('Camera error:', error);
      setInputMethod('manual');
    } finally {
      setIsProcessing(false);
    }
  };

  const stopWebcam = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach(track => track.stop());
      setCameraStream(null);
    }
    setInputMethod('manual');
  };

  const startEmotionDetection = () => {
    // Simulated emotion detection (replace with real face analysis)
    const detectionInterval = setInterval(() => {
      if (!cameraStream) {
        clearInterval(detectionInterval);
        return;
      }

      const simulatedEmotion = {
        joy: Math.max(0, Math.min(1, emotion.joy + (Math.random() - 0.5) * 0.1)),
        calm: Math.max(0, Math.min(1, emotion.calm + (Math.random() - 0.5) * 0.1)),
        energy: Math.max(0, Math.min(1, emotion.energy + (Math.random() - 0.5) * 0.1)),
        melancholy: Math.max(0, Math.min(1, emotion.melancholy + (Math.random() - 0.5) * 0.1))
      };
      
      onChange(simulatedEmotion);
    }, 1000);

    return () => clearInterval(detectionInterval);
  };

  // Voice Input
  const startVoice = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.error('Speech recognition not supported');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.lang = 'en-US';

    const emotionKeywords = {
      joy: ['happy', 'excited', 'wonderful', 'great', 'amazing', 'joy', 'delighted'],
      calm: ['peaceful', 'relaxed', 'serene', 'quiet', 'calm', 'tranquil'],
      energy: ['energetic', 'active', 'dynamic', 'powerful', 'strong', 'vigorous'],
      melancholy: ['sad', 'down', 'melancholy', 'blue', 'lonely', 'depressed', 'unhappy']
    };

    recognition.onresult = (event) => {
      const transcript = event.results[event.results.length - 1][0].transcript.toLowerCase();
      const newEmotion = { ...emotion };
      
      Object.entries(emotionKeywords).forEach(([type, keywords]) => {
        keywords.forEach(keyword => {
          if (transcript.includes(keyword)) {
            newEmotion[type] = Math.min(1, newEmotion[type] + 0.2);
          }
        });
      });

      onChange(newEmotion);
    };

    recognition.start();
    setVoiceRecognition(recognition);
    setInputMethod('voice');
  };

  const stopVoice = () => {
    if (voiceRecognition) {
      voiceRecognition.stop();
      setVoiceRecognition(null);
    }
    setInputMethod('manual');
  };

  return (
    <div className="emotion-input">
      <h3>Express Your Emotions</h3>
      
      <div className="input-methods">
        <button 
          onClick={() => setInputMethod('manual')}
          className={`method-button ${inputMethod === 'manual' ? 'active' : ''}`}
        >
          🎚️ Manual Control
        </button>
        <button 
          onClick={inputMethod === 'webcam' ? stopWebcam : startWebcam}
          className={`method-button ${inputMethod === 'webcam' ? 'active' : ''}`}
          disabled={isProcessing}
        >
          📹 {inputMethod === 'webcam' ? 'Stop Camera' : 'Use Camera'}
        </button>
        <button 
          onClick={inputMethod === 'voice' ? stopVoice : startVoice}
          className={`method-button ${inputMethod === 'voice' ? 'active' : ''}`}
        >
          🎤 {inputMethod === 'voice' ? 'Stop Voice' : 'Use Voice'}
        </button>
      </div>

      {inputMethod === 'webcam' && (
        <div className="webcam-container">
          <video 
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="webcam-feed"
          />
        </div>
      )}

      {inputMethod === 'voice' && (
        <div className="voice-indicator">
          🎤 Listening for emotion keywords...
          <div className="keyword-hints">
            Try saying: "I feel happy", "I'm excited", "feeling peaceful"...
          </div>
        </div>
      )}

      <div className="emotion-sliders" style={{ opacity: inputMethod === 'manual' ? 1 : 0.5 }}>
        {Object.entries(emotion).map(([emotionType, value]) => (
          <div key={emotionType} className="emotion-slider">
            <label>
              <span className="emotion-name">
                {emotionType.charAt(0).toUpperCase() + emotionType.slice(1)}
              </span>
              <span className="emotion-value">{Math.round(value * 100)}%</span>
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={value}
              onChange={(e) => handleSliderChange(emotionType, parseFloat(e.target.value))}
              className={`slider ${emotionType}`}
              disabled={inputMethod !== 'manual'}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default EmotionInput;
