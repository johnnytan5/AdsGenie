'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import LiquidEther from '@/components/LiquidEther';
import CursorGenie from '@/components/CursorGenie';
import Lottie from 'lottie-react';

export default function Home() {
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [genieAnimationData, setGenieAnimationData] = useState<any>(null);
  const router = useRouter();

  // Load genie animation for logo
  useEffect(() => {
    fetch('/genie.json')
      .then((res) => res.json())
      .then((data) => setGenieAnimationData(data))
      .catch((err) => console.error('Failed to load genie animation:', err));
  }, []);

  const handleMyProjects = () => {
    setIsTransitioning(true);
    // Wait for transition animation to complete, then navigate
    setTimeout(() => {
      router.push('/projects');
    }, 700); // Match the transition duration
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Cursor Following Genie */}
      <CursorGenie />
      
      {/* LiquidEther Backdrop */}
      <div style={{ width: '100%', height: '100%', position: 'fixed', top: 0, left: 0, zIndex: 0 }}>
        <LiquidEther
          colors={['#5227FF', '#FF9FFC', '#B19EEF']}
          mouseForce={20}
          cursorSize={100}
          isViscous={false}
          viscous={30}
          iterationsViscous={32}
          iterationsPoisson={32}
          resolution={0.5}
          isBounce={false}
          autoDemo={true}
          autoSpeed={0.5}
          autoIntensity={2.2}
          takeoverDuration={0.25}
          autoResumeDelay={3000}
          autoRampDuration={0.6}
        />
      </div>

      {/* Main Content Container - Moves up when transitioning */}
      <div className={`relative z-10 transition-transform duration-700 ease-out ${isTransitioning ? '-translate-y-[50vh]' : 'translate-y-0'}`}>
        {/* Hero Section - Stays centered */}
        <div className="min-h-screen flex items-center justify-center p-4">
          <div className="max-w-2xl w-full text-center space-y-8">
            <div className="space-y-4">
              {/* Genie Logo */}
              {genieAnimationData && (
                <div className="flex justify-center mb-2">
                  <div style={{ width: '120px', height: '120px' }}>
                    <Lottie
                      animationData={genieAnimationData}
                      loop={true}
                      autoplay={true}
                      style={{ width: '100%', height: '100%' }}
                    />
                  </div>
                </div>
              )}
              <h1 className="text-5xl font-bold text-slate-900">Ads Genie</h1>
              <p className="text-xl text-slate-600">
                Let the genie grant your video wishes
              </p>
            </div>
            
            <div className="flex justify-center items-center">
              <Button 
                size="lg" 
                className="w-full sm:w-auto min-w-[200px]"
                onClick={handleMyProjects}
                disabled={isTransitioning}
                style={{
                  backgroundColor: '#5227FF',
                  color: 'white',
                  border: 'none',
                }}
                onMouseEnter={(e) => {
                  if (!isTransitioning) {
                    e.currentTarget.style.backgroundColor = '#4218E6';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isTransitioning) {
                    e.currentTarget.style.backgroundColor = '#5227FF';
                  }
                }}
              >
                My Projects
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
