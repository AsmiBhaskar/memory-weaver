// src/components/EnvironmentVisualizer.js
import React, { useEffect, useRef } from "react";

const EnvironmentVisualizer = ({ emotion }) => {
  const canvasRef = useRef(null);
  const requestRef = useRef(null);

  const colors = {
    joy: [255, 215, 0],        // gold
    calm: [79, 195, 247],      // light blue
    melancholy: [156, 39, 176] // purple
  };

  const getBackgroundColor = () => {
    const { joy, calm, melancholy } = emotion;
    const total = joy + calm + melancholy || 1;
    const r = Math.round(
      (joy * colors.joy[0] + calm * colors.calm[0] + melancholy * colors.melancholy[0]) / total
    );
    const g = Math.round(
      (joy * colors.joy[1] + calm * colors.calm[1] + melancholy * colors.melancholy[1]) / total
    );
    const b = Math.round(
      (joy * colors.joy[2] + calm * colors.calm[2] + melancholy * colors.melancholy[2]) / total
    );
    return `rgb(${r}, ${g}, ${b})`;
  };

  // Map top 2 emotions to combined names
  const getEmotionName = () => {
    const entries = Object.entries(emotion).sort((a, b) => b[1] - a[1]);
    const [first, second] = entries;
    if (!first) return "Neutral";

    // If second emotion is close, combine names
    if (second && first[1] - second[1] < 0.3) {
      const combinationMap = {
        "joy|calm": "Happily Calm",
        "calm|joy": "Happily Calm",
        "joy|melancholy": "Bittersweet",
        "melancholy|joy": "Bittersweet",
        "calm|melancholy": "Peaceful Sadness",
        "melancholy|calm": "Peaceful Sadness"
      };
      const key = `${first[0]}|${second[0]}`;
      return combinationMap[key] || "Mixed Feeling";
    }

    return first[0]; // dominant emotion
  };

  const animate = (ctx, width, height, time) => {
    const { calm, energy } = emotion;

    ctx.fillStyle = getBackgroundColor();
    ctx.fillRect(0, 0, width, height);

    const waveCount = Math.floor(1 + energy * 3);

    for (let i = 0; i < waveCount; i++) {
      const amplitude = 10 + calm * 30;
      const frequency = 0.02 + energy * 0.05;
      const speed = 0.02 + energy * 0.08;

      ctx.beginPath();
      for (let x = 0; x < width; x++) {
        const y =
          height / 2 +
          amplitude *
            Math.sin(frequency * x + speed * time + i) *
            (0.5 + Math.random() * 0.5);
        ctx.lineTo(x, y);
      }
      ctx.strokeStyle = "#ffffff";
      ctx.globalAlpha = 0.3 + 0.2 * i;
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    ctx.globalAlpha = 1;
    ctx.fillStyle = "#ffffff";
    ctx.font = "20px Arial";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(getEmotionName(), width / 2, height / 2);
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    const resize = () => {
      canvas.width = canvas.clientWidth;
      canvas.height = canvas.clientHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    let time = 0;
    const render = () => {
      time += 1;
      animate(ctx, canvas.width, canvas.height, time);
      requestRef.current = requestAnimationFrame(render);
    };
    render();

    return () => {
      cancelAnimationFrame(requestRef.current);
      window.removeEventListener("resize", resize);
    };
  }, [emotion]);

  return (
    <div
      className="environment-visualizer"
      style={{
        height: "200px",
        borderRadius: "10px",
        margin: "20px 0",
        position: "relative",
        overflow: "hidden"
      }}
    >
      <canvas
        ref={canvasRef}
        style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%" }}
      />
    </div>
  );
};

export default EnvironmentVisualizer;

