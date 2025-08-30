// src/components/ParticleSystem.js
import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';

const ParticleSystem = ({ emotion }) => {
  const mesh = useRef();
  const particleCount = 500;
  const particles = useMemo(() => {
    const temp = [];
    for (let i = 0; i < particleCount; i++) {
      const x = (Math.random() - 0.5) * 20;
      const y = (Math.random() - 0.5) * 20;
      const z = (Math.random() - 0.5) * 20;
      temp.push(x, y, z);
    }
    return new Float32Array(temp);
  }, []);

  useFrame(({ clock }) => {
    const time = clock.getElapsedTime();
    const positions = mesh.current.geometry.attributes.position.array;
    for (let i = 0; i < particleCount; i++) {
      const i3 = i * 3;
      if (emotion.joy > 0.5) positions[i3 + 1] += Math.sin(time + i) * 0.01 * emotion.joy;
      if (emotion.energy > 0.5) {
        positions[i3] += Math.cos(time * 2 + i) * 0.005 * emotion.energy;
        positions[i3 + 2] += Math.sin(time * 2 + i) * 0.005 * emotion.energy;
      }
      if (emotion.calm > 0.5) positions[i3] += Math.cos(time * 0.5 + i) * 0.002 * emotion.calm;
    }
    mesh.current.geometry.attributes.position.needsUpdate = true;
  });

  const particleColor = useMemo(() => {
    const { joy, calm, energy, melancholy } = emotion;
    if (joy > 0.6) return '#FFD700';
    if (calm > 0.6) return '#4FC3F7';
    if (energy > 0.6) return '#FF6B35';
    if (melancholy > 0.6) return '#9C27B0';
    const r = joy * 255 + energy * 255;
    const g = joy * 215 + calm * 195 + energy * 107;
    const b = calm * 247 + melancholy * 176;
    return `rgb(${Math.min(255, r)}, ${Math.min(255, g)}, ${Math.min(255, b)})`;
  }, [emotion]);

  return (
    <points ref={mesh}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={particleCount}
          array={particles}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.05}
        color={particleColor}
        transparent={true}
        opacity={0.8}
      />
    </points>
  );
};

export const ParticleCanvas = ({ emotion }) => (
  <Canvas style={{ height: '300px', borderRadius: '10px', margin: '20px 0' }}>
    <ParticleSystem emotion={emotion} />
  </Canvas>
);

export default ParticleSystem;
