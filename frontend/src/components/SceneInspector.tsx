'use client';

import { useState, useEffect } from 'react';
import { useProjectStore } from '@/store/projectStore';
import { Input } from './ui/Input';
import { Textarea } from './ui/Textarea';
import { FileUpload } from './ui/FileUpload';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { Switch } from './ui/Switch';

interface SceneInspectorProps {
  sceneId: string | null;
}

export const SceneInspector: React.FC<SceneInspectorProps> = ({ sceneId }) => {
  const { currentProject, updateScene, generateSceneImage, generateSceneVideo, setScene } = useProjectStore();
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);

  // Find the scene (will be null if not found)
  const scene = currentProject?.scenes.find((s) => s.id === sceneId) || null;

  // Reset loading states when generation completes
  // This hook must be called unconditionally (before any early returns)
  useEffect(() => {
    if (!scene) return;
    
    if (scene.generatedImage && isGeneratingImage) {
      setIsGeneratingImage(false);
    }
    if (scene.generatedVideo && isGeneratingVideo) {
      setIsGeneratingVideo(false);
    }
    if (scene.status === 'done' || scene.status === 'failed') {
      setIsGeneratingImage(false);
      setIsGeneratingVideo(false);
    }
  }, [scene?.generatedImage, scene?.generatedVideo, scene?.status, isGeneratingImage, isGeneratingVideo, scene]);

  // Early returns after all hooks
  if (!currentProject || !sceneId) {
    return (
      <div className="w-80 bg-white border-l border-slate-200 h-full flex items-center justify-center">
        <p className="text-slate-400 text-sm">Select a scene to edit</p>
      </div>
    );
  }

  if (!scene) return null;

  const handleSceneChange = (field: string, value: any) => {
    // Only update local state - no API calls
    setScene(sceneId, { [field]: value });
  };

  const handleUpdate = async (updates: Partial<typeof scene>) => {
    // For now, keep updateScene for when we need to save to backend
    // But prefer handleSceneChange for local-only updates
    await updateScene(sceneId, updates);
  };

  const handleRegenerateImage = async () => {
    setIsGeneratingImage(true);
    try {
      await generateSceneImage(sceneId);
    } finally {
      // Keep loading state until webhook updates (or timeout)
      setTimeout(() => setIsGeneratingImage(false), 30000);
    }
  };

  const handleRegenerateVideo = async () => {
    if (!currentProject) return;
    setIsGeneratingVideo(true);
    try {
      // Save scene data first (description, duration) before generating
      // This ensures the backend has the latest scene data
      await updateScene(sceneId, {
        description: scene.description,
        duration: scene.duration,
      });
      
      // Toggles are read from scene, not passed as parameters
      await generateSceneVideo(sceneId, currentProject.aspectRatio);
    } finally {
      // Keep loading state until webhook updates (or timeout)
      setTimeout(() => setIsGeneratingVideo(false), 30000);
    }
  };

  return (
    <div className="w-80 bg-white border-l border-slate-200 h-full overflow-y-auto p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-slate-900">Scene Inspector</h2>
        <p className="text-sm text-slate-500 mt-1">Scene {scene.order}</p>
      </div>

      <div className="space-y-6">
        {/* Video Preview */}
        {scene.generatedVideo && (
          <Card className="p-4">
            <h3 className="text-sm font-medium text-slate-900 mb-3">Video Preview</h3>
            <video
              src={scene.generatedVideo}
              controls
              className="w-full rounded-lg"
            />
          </Card>
        )}

        {/* Image/Video Actions */}
        <Card className="p-4">
          <h3 className="text-sm font-medium text-slate-900 mb-4">Media</h3>
          <div className="space-y-4">
            <Textarea
              label="Image Description"
              value={scene.imageDescription || ''}
              onChange={(e) => handleSceneChange('imageDescription', e.target.value)}
              placeholder="Describe the image you want to generate for this scene..."
              rows={3}
            />
            
            <FileUpload
              label="Upload Sketch/Image"
              accept="image/*"
              currentFile={scene.sketch}
              onChange={(file) => handleSceneChange('sketch', file)}
            />
            
            {/* Global Character/Setting Toggles for Image Generation */}
            <div className="space-y-2 pt-2 border-t border-slate-200">
              <p className="text-xs font-medium text-slate-700">Image Generation Options</p>
              <Switch
                label="Use Global Character"
                checked={scene.useGlobalCharacterForImage || false}
                onChange={(checked) => handleUpdate({ useGlobalCharacterForImage: checked })}
              />
              <Switch
                label="Use Global Setting"
                checked={scene.useGlobalSettingForImage || false}
                onChange={(checked) => handleUpdate({ useGlobalSettingForImage: checked })}
              />
              {(scene.useGlobalCharacterForImage || scene.useGlobalSettingForImage) && (
                <p className="text-xs text-slate-500 mt-1">
                  Using Gemini 3 Pro Preview for multi-image generation
                </p>
              )}
            </div>
            
            {scene.generatedImage && (
              <div>
                <p className="text-xs text-slate-600 mb-2">Generated Image</p>
                <img
                  src={scene.generatedImage}
                  alt="Scene"
                  className="w-full rounded-lg border border-slate-200"
                />
              </div>
            )}
            
            {scene.sketchS3Url && !scene.generatedImage && (
              <div>
                <p className="text-xs text-slate-600 mb-2">Sketch</p>
                <img
                  src={scene.sketchS3Url}
                  alt="Scene Sketch"
                  className="w-full rounded-lg border border-slate-200 opacity-50"
                />
                {scene.status === 'processing' && (
                  <p className="text-xs text-slate-500 mt-1">Generating image...</p>
                )}
              </div>
            )}
            
            <div className="flex flex-col gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRegenerateImage}
                className="w-full"
                disabled={((!scene.imageDescription || scene.imageDescription.trim() === '') && !scene.sketch && !scene.sketchS3Url) || isGeneratingImage || scene.status === 'processing'}
                loading={isGeneratingImage || scene.status === 'processing'}
              >
                {(isGeneratingImage || scene.status === 'processing') ? 'Generating...' : 'Generate Image'}
              </Button>
              
              {(!scene.imageDescription || scene.imageDescription.trim() === '') && !scene.sketch && !scene.sketchS3Url && (
                <p className="text-xs text-slate-500 mt-1">Please provide an image description or upload a sketch to generate an image</p>
              )}
              
              {scene.status === 'failed' && (
                <p className="text-xs text-red-600">Generation failed. Please try again.</p>
              )}
            </div>
          </div>
        </Card>

        {/* Scene Details */}
        <Card className="p-4">
          <h3 className="text-sm font-medium text-slate-900 mb-4">Scene</h3>
          <div className="space-y-4">
            <Input
              label="Duration (seconds)"
              type="number"
              value={scene.duration}
              onChange={(e) => handleSceneChange('duration', Number(e.target.value))}
              min="1"
            />
            
            <Textarea
              label="Scene Description"
              value={scene.description === 'New Scene' ? '' : scene.description}
              onChange={(e) => handleSceneChange('description', e.target.value || 'New Scene')}
              placeholder="Describe what happens in this scene..."
              rows={4}
            />
          </div>
        </Card>

        {/* Audio Settings */}
        <Card className="p-4">
          <h3 className="text-sm font-medium text-slate-900 mb-4">Audio</h3>
          <div className="space-y-6">
            {/* Voiceover Toggle */}
            <Switch
              label="Voiceover"
              checked={scene.voiceoverEnabled || false}
              onChange={(checked) => handleUpdate({ voiceoverEnabled: checked })}
            />

            {/* Voiceover Options - Only show if enabled */}
            {scene.voiceoverEnabled && (
              <div className="space-y-4 pl-4 border-l-2 border-slate-200">
                <Textarea
                  label="Narration"
                  value={scene.voiceoverText || ''}
                  onChange={(e) => handleUpdate({ voiceoverText: e.target.value })}
                  placeholder="Enter the narration text for this scene..."
                  rows={4}
                />
                
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-slate-700">
                    Voice Gender
                  </label>
                  <div className="flex gap-4">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name={`voiceover-gender-${scene.id}`}
                        value="male"
                        checked={scene.voiceoverGender === 'male'}
                        onChange={() => handleUpdate({ voiceoverGender: 'male' })}
                        className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-slate-700">Male</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name={`voiceover-gender-${scene.id}`}
                        value="female"
                        checked={scene.voiceoverGender === 'female'}
                        onChange={() => handleUpdate({ voiceoverGender: 'female' })}
                        className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-slate-700">Female</span>
                    </label>
                  </div>
                </div>
              </div>
            )}

            {/* Background Music Toggle */}
            <Switch
              label="Background Music"
              checked={scene.backgroundMusicEnabled || false}
              onChange={(checked) => handleUpdate({ backgroundMusicEnabled: checked })}
            />
          </div>
        </Card>

        {/* Generate Scene Video - Independent at bottom */}
        <div className="pt-4 border-t border-slate-200 space-y-4">
          {/* Video Generation Options */}
          <div className="space-y-2">
            <p className="text-xs font-medium text-slate-700">Video Generation Options</p>
            <Switch
              label="Use Global Character"
              checked={scene.useGlobalCharacterForVideo || false}
              onChange={(checked) => handleUpdate({ useGlobalCharacterForVideo: checked })}
            />
            <Switch
              label="Use Global Setting"
              checked={scene.useGlobalSettingForVideo || false}
              onChange={(checked) => handleUpdate({ useGlobalSettingForVideo: checked })}
            />
          </div>
          
          <Button
            variant="primary"
            size="sm"
            onClick={handleRegenerateVideo}
            className="w-full"
            disabled={(!scene.generatedImage || !scene.description || scene.description === 'New Scene' || scene.description.trim() === '') || isGeneratingVideo || scene.status === 'processing'}
            loading={isGeneratingVideo || scene.status === 'processing'}
          >
            {(isGeneratingVideo || scene.status === 'processing') ? 'Generating...' : 'Generate Scene Video'}
          </Button>
          
          {(!scene.generatedImage || !scene.description || scene.description === 'New Scene' || scene.description.trim() === '') && (
            <p className="text-xs text-slate-500 mt-1">Scene must have a generated image and valid description to generate video</p>
          )}
          
          {scene.status === 'failed' && (
            <p className="text-xs text-red-600 mt-1">Video generation failed. Please check the backend logs and try again.</p>
          )}
          
          {scene.status === 'processing' && !isGeneratingVideo && (
            <p className="text-xs text-blue-600 mt-1">Video generation in progress...</p>
          )}
        </div>
      </div>
    </div>
  );
};

