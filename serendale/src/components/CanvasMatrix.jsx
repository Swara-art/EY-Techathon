import { useRef, useEffect } from "react";

export default function CanvasMatrix() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const state = {
      fps: 30,
      bgOpacity: 0.05,
      color: "rgba(42, 0, 242, 0.3)",
      charset: "01",
      size: 20
    };

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    let w, h, colYPos;

    const resize = () => {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
      const numCols = Math.ceil(w / state.size);
      colYPos = Array(numCols).fill(0);
    };

    window.addEventListener("resize", resize);

    resize();

    const random = (items) => items[Math.floor(Math.random() * items.length)];
    const randomRange = (start, end) => start + end * Math.random();

    const draw = () => {
      ctx.fillStyle = `rgba(0,0,0,${state.bgOpacity})`;
      ctx.fillRect(0, 0, w, h);

      ctx.fillStyle = state.color;
      ctx.font = state.size + "px monospace";

      for (let i = 0; i < colYPos.length; i++) {
        const yPos = colYPos[i];
        const xPos = i * state.size;
        ctx.fillText(random(state.charset), xPos, yPos);

        const reachedBottom = yPos >= h;
        const randomReset = yPos >= randomRange(100, 5000);
        if (reachedBottom || randomReset) {
          colYPos[i] = 0;
        } else {
          colYPos[i] = yPos + state.size;
        }
      }
    };

    let intervalId = setInterval(draw, 1000 / state.fps);

    return () => {
      clearInterval(intervalId);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return <canvas ref={canvasRef} id="canvas" style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', zIndex: 0 }} />;
}
