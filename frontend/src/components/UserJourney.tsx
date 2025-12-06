'use client';

import { useProjectStore } from '@/store/projectStore';
import { Check } from 'lucide-react';

type StepStatus = 'completed' | 'current' | 'pending';

interface Step {
  id: string;
  label: string;
  status: StepStatus;
}

export function UserJourney() {
  const { currentProject } = useProjectStore();

  if (!currentProject) return null;

  // Determine step statuses
  const steps: Step[] = [];

  // Step 1: Select Aspect Ratio
  const aspectRatioCompleted = !!currentProject.aspectRatio;
  steps.push({
    id: 'aspect-ratio',
    label: 'Select Aspect Ratio',
    status: aspectRatioCompleted ? 'completed' : 'current',
  });

  // Step 2: Configure Global Variables
  const globalCharacterCompleted = !!currentProject.globalSettings?.character?.image;
  const globalSettingCompleted = !!currentProject.globalSettings?.setting?.image;
  const globalVariablesCompleted = globalCharacterCompleted && globalSettingCompleted;
  const globalVariablesCurrent = aspectRatioCompleted && !globalVariablesCompleted;
  steps.push({
    id: 'global-variables',
    label: 'Configure Global Variables',
    status: globalVariablesCompleted
      ? 'completed'
      : globalVariablesCurrent
      ? 'current'
      : 'pending',
  });

  // Step 3: Configure Scene Information
  const hasScenes = currentProject.scenes.length > 0;
  // A scene is considered fully configured if it has BOTH an image AND a description
  // Scene info is completed only when ALL scenes are fully configured
  const allScenesConfigured = hasScenes
    ? currentProject.scenes.every(
        (scene) =>
          (scene.generatedImage || scene.sketchS3Url || (scene.imageDescription && scene.imageDescription.trim() !== '')) &&
          (scene.description && scene.description.trim() !== '' && scene.description !== 'New Scene')
      )
    : false;
  const sceneInfoCompleted = hasScenes && allScenesConfigured;
  // Current if global variables are done AND (no scenes yet OR scenes exist but not all configured)
  const sceneInfoCurrent = globalVariablesCompleted && !sceneInfoCompleted;
  steps.push({
    id: 'scene-information',
    label: 'Configure Scene Information',
    status: sceneInfoCompleted
      ? 'completed'
      : sceneInfoCurrent
      ? 'current'
      : 'pending',
  });

  // Step 4: Configure Voice and Music (optional step - can be skipped)
  // This step is considered completed if at least one scene has voice or music configured
  // Current ONLY if scene info is completed AND voice/music is not configured
  const hasVoiceOrMusic = currentProject.scenes.some(
    (scene) => scene.voiceoverEnabled || scene.backgroundMusicEnabled
  );
  const voiceMusicCompleted = hasVoiceOrMusic;
  // Only current if scene info is completed (not just if scenes exist)
  const voiceMusicCurrent = sceneInfoCompleted && !voiceMusicCompleted;
  steps.push({
    id: 'voice-music',
    label: 'Configure Voice and Music',
    status: voiceMusicCompleted
      ? 'completed'
      : voiceMusicCurrent
      ? 'current'
      : 'pending',
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
                          ? 'w-7 h-7 rounded-full bg-slate-900 border-slate-900 flex items-center justify-center'
                          : step.status === 'current'
                          ? 'w-8 h-8 rounded-full bg-blue-600 border-2 border-blue-600 shadow-lg shadow-blue-600/30 flex items-center justify-center'
                          : 'w-7 h-7 rounded-full bg-white border border-slate-300 flex items-center justify-center'
                      }`}
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
                          ? 'bg-slate-900'
                          : 'bg-slate-200'
                      }`}
                    />
                  )}
                </div>
                {/* Label - positioned directly below the circle, centered */}
                <span
                  className={`mt-3 text-xs font-medium text-center whitespace-nowrap ${
                    step.status === 'completed'
                      ? 'text-slate-700'
                      : step.status === 'current'
                      ? 'text-blue-600 font-semibold'
                      : 'text-slate-500'
                  }`}
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
