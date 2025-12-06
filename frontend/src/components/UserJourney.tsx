'use client';

import { usePathname } from 'next/navigation';
import { Check } from 'lucide-react';

type StepStatus = 'completed' | 'current' | 'pending';

interface Step {
  id: string;
  label: string;
  status: StepStatus;
}

export function UserJourney() {
  const pathname = usePathname();

  // Determine step statuses based on current pathname
  const steps: Step[] = [];

  const isAspectRatioPage = pathname === '/aspect-ratio';
  const isEditorPage = pathname?.startsWith('/editor/');
  const isAudioPage = pathname === '/audio';

  // Step 1: Select Aspect Ratio
  steps.push({
    id: 'aspect-ratio',
    label: 'Select Aspect Ratio',
    status: isAspectRatioPage ? 'current' : (isEditorPage || isAudioPage) ? 'completed' : 'pending',
  });

  // Step 2: Configure Global Variables
  // Completed if on editor or audio page (since you configure global vars in editor before scenes)
  steps.push({
    id: 'global-variables',
    label: 'Configure Global Variables',
    status: isEditorPage || isAudioPage ? 'completed' : 'pending',
  });

  // Step 3: Configure Scene Information
  // Current if on editor page, completed if on audio page
  steps.push({
    id: 'scene-information',
    label: 'Configure Scene Information',
    status: isEditorPage ? 'current' : isAudioPage ? 'completed' : 'pending',
  });

  // Step 4: Configure Voice and Music
  // Current if on audio page
  steps.push({
    id: 'voice-music',
    label: 'Configure Voice and Music',
    status: isAudioPage ? 'current' : 'pending',
  });

  return (
    <div className="bg-slate-50 border-b border-slate-200 px-6 py-4">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-start">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-start flex-1">
              {/* Step Circle and Label Container */}
              <div className="flex flex-col items-center flex-1 relative">
                {/* Top section with circle and connector */}
                <div className="flex items-center w-full">
                  {/* Step Circle - centered */}
                  <div className="flex-shrink-0 flex flex-col items-center">
                    <div
                      className={`transition-all duration-200 ${
                        step.status === 'completed'
                          ? 'w-7 h-7 rounded-full bg-purple-600 border-purple-600 flex items-center justify-center'
                          : step.status === 'current'
                          ? 'w-8 h-8 rounded-full bg-purple-600 border-2 border-purple-600 shadow-lg shadow-purple-600/30 flex items-center justify-center'
                          : 'w-7 h-7 rounded-full bg-white border border-slate-300 flex items-center justify-center'
                      }`}
                      style={{
                        backgroundColor: step.status === 'completed' ? '#5227FF' : step.status === 'current' ? '#5227FF' : undefined,
                        borderColor: step.status === 'completed' ? '#5227FF' : step.status === 'current' ? '#5227FF' : undefined,
                        boxShadow: step.status === 'current' ? '0 10px 15px -3px rgba(82, 39, 255, 0.3), 0 4px 6px -2px rgba(82, 39, 255, 0.3)' : undefined,
                      }}
                    >
                      {step.status === 'completed' ? (
                        <Check className="w-3.5 h-3.5 text-white" strokeWidth={2.5} />
                      ) : step.status === 'current' ? (
                        <div className="w-2 h-2 rounded-full bg-white" />
                      ) : (
                        <div className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                      )}
                    </div>
                  </div>

                  {/* Connector Line */}
                  {index < steps.length - 1 && (
                    <div
                      className={`flex-1 h-px mx-3 ${
                        step.status === 'completed'
                          ? 'bg-purple-600'
                          : 'bg-slate-200'
                      }`}
                      style={{
                        backgroundColor: step.status === 'completed' ? '#5227FF' : undefined,
                      }}
                    />
                  )}
                </div>
                {/* Label - positioned directly below the circle, centered */}
                <span
                  className={`mt-3 text-xs font-medium text-center whitespace-nowrap ${
                    step.status === 'completed'
                      ? 'text-purple-700'
                      : step.status === 'current'
                      ? 'text-purple-600 font-semibold'
                      : 'text-slate-500'
                  }`}
                  style={{
                    color: step.status === 'completed' ? '#5227FF' : step.status === 'current' ? '#5227FF' : undefined,
                  }}
                >
                  {step.label}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
