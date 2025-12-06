'use client';

import { useEffect, useState, useRef } from 'react';
import Lottie from 'lottie-react';

interface CursorGenieProps {
  size?: number; // Size in pixels, default 120
}

export default function CursorGenie({ size = 120 }: CursorGenieProps) {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isVisible, setIsVisible] = useState(false);
  const [animationData, setAnimationData] = useState<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const rafRef = useRef<number | null>(null);
  const targetPositionRef = useRef({ x: 0, y: 0 });
  const currentPositionRef = useRef({ x: 0, y: 0 });

  // Load the Lottie animation data
  useEffect(() => {
    fetch('/genie.json')
      .then((res) => res.json())
      .then((data) => setAnimationData(data))
      .catch((err) => console.error('Failed to load genie animation:', err));
  }, []);

  // Smooth animation loop using requestAnimationFrame
  useEffect(() => {
    const animate = () => {
      const currentX = currentPositionRef.current.x;
      const currentY = currentPositionRef.current.y;
      const targetX = targetPositionRef.current.x;
      const targetY = targetPositionRef.current.y;

      // Use a faster lerp for more responsive movement
      const lerpFactor = 0.4; // Higher = more responsive (0-1)
      const newX = currentX + (targetX - currentX) * lerpFactor;
      const newY = currentY + (targetY - currentY) * lerpFactor;

      currentPositionRef.current = { x: newX, y: newY };
      setPosition({ x: newX, y: newY });

      rafRef.current = requestAnimationFrame(animate);
    };

    rafRef.current = requestAnimationFrame(animate);

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      targetPositionRef.current = { x: e.clientX, y: e.clientY };
      setIsVisible(true);
    };

    const handleMouseLeave = () => {
      setIsVisible(false);
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    document.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, []);

  if (!isVisible || !animationData) return null;

  return (
    <div
      ref={containerRef}
      className="fixed pointer-events-none z-50 will-change-transform"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        transform: 'translate(-50%, -50%)',
        width: `${size}px`,
        height: `${size}px`,
      }}
    >
      <Lottie
        animationData={animationData}
        loop={true}
        autoplay={true}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
}

