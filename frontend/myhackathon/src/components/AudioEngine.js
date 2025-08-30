// src/components/AudioEngine.js
import React, { useEffect } from 'react';

const AudioEngine = ({ emotion }) => {
  useEffect(() => {
    // Simple audio feedback based on dominant emotion
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    let oscillator = ctx.createOscillator();
    let gain = ctx.createGain();
    oscillator.connect(gain);
    gain.connect(ctx.destination);

    // Pick frequency and waveform based on emotion
    let freq = 440;
    let type = 'sine';
    if (emotion.joy > 0.6) { freq = 880; type = 'triangle'; }
    if (emotion.calm > 0.6) { freq = 220; type = 'sine'; }
    if (emotion.energy > 0.6) { freq = 660; type = 'square'; }
    if (emotion.melancholy > 0.6) { freq = 330; type = 'sawtooth'; }
    oscillator.frequency.value = freq;
    oscillator.type = type;
    gain.gain.value = 0.05;
    oscillator.start();
    setTimeout(() => {
      oscillator.stop();
      ctx.close();
    }, 500);
    // Clean up
    return () => {
      oscillator.stop();
      ctx.close();
    };
  }, [emotion]);

  return (
    <div className="audio-engine">
      <h4>Audio Feedback</h4>
      <p>Plays a tone based on emotion!</p>
    </div>
  );
};

export default AudioEngine;
