// src/components/AudioEngine.js
import React, { useState, useEffect, useRef } from 'react';

const AudioEngine = ({ emotion }) => {
  const audioContextRef = useRef(null);
  const oscillatorRef = useRef(null);
  const timeoutRef = useRef(null);
  const [isEnabled, setIsEnabled] = useState(false);

  const playSound = () => {
    setIsEnabled(true);
  };

  useEffect(() => {
    if (!isEnabled) return;
    // Clean up previous audio
    const cleanup = () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
      
      if (oscillatorRef.current) {
        try {
          oscillatorRef.current.stop();
        } catch (e) {
          // Ignore if already stopped
        }
        oscillatorRef.current = null;
      }

      if (audioContextRef.current?.state !== 'closed') {
        try {
          audioContextRef.current?.close();
        } catch (e) {
          // Ignore if already closed
        }
      }
    };

    // Clean up previous before creating new
    cleanup();

    // Create new audio context
    try {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      oscillatorRef.current = audioContextRef.current.createOscillator();
      const gain = audioContextRef.current.createGain();
      
      oscillatorRef.current.connect(gain);
      gain.connect(audioContextRef.current.destination);

      // Pick frequency and waveform based on emotion
      let freq = 440;
      let type = 'sine';
      
      // Find dominant emotion
      const emotions = Object.entries(emotion);
      const dominantEmotion = emotions.reduce((max, [key, value]) => 
        value > max.value ? { key, value } : max,
        { key: '', value: -1 }
      );

      switch (dominantEmotion.key) {
        case 'joy':
          freq = 880;
          type = 'triangle';
          break;
        case 'calm':
          freq = 220;
          type = 'sine';
          break;
        case 'energy':
          freq = 660;
          type = 'square';
          break;
        case 'melancholy':
          freq = 330;
          type = 'sawtooth';
          break;
      }

      oscillatorRef.current.frequency.value = freq;
      oscillatorRef.current.type = type;
      gain.gain.value = 0.05;

      oscillatorRef.current.start();
      
      // Schedule stop
      timeoutRef.current = setTimeout(() => {
        cleanup();
      }, 500);
    } catch (error) {
      console.error('Audio initialization error:', error);
    }

    // Cleanup on unmount or emotion change
    return cleanup;
  }, [emotion]);

  return (
    <div className="audio-engine">
      <h4>Audio Feedback</h4>
      <button 
        onClick={playSound} 
        className={`sound-toggle ${isEnabled ? 'active' : ''}`}
      >
        {isEnabled ? '🔊 Sound On' : '🔇 Enable Sound'}
      </button>
      {isEnabled && (
        <div className="emotion-tone-info">
          <small>
            Joy: High pitch triangle wave<br />
            Calm: Low pitch sine wave<br />
            Energy: Medium pitch square wave<br />
            Melancholy: Low-mid pitch sawtooth wave
          </small>
        </div>
      )}
    </div>
  );
};

export default AudioEngine;
