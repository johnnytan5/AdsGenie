'use client';

import { useState, useEffect } from 'react';
import { useProjectStore } from '@/store/projectStore';
import { Input } from './ui/Input';
import { Textarea } from './ui/Textarea';
import { FileUpload } from './ui/FileUpload';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { Switch } from './ui/Switch';
import { ExcalidrawModal } from './ExcalidrawModal';
import { Pencil } from 'lucide-react';

interface SceneInspectorProps {
  sceneId: string | null;
}

export const SceneInspector: React.FC<SceneInspectorProps> = ({ sceneId }) => {
  const { currentProject, updateScene, generateSceneImage, generateSceneVideo, setScene } = useProjectStore();
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);
  const [isExcalidrawOpen, setIsExcalidrawOpen] = useState(false);
  const [sceneImageLoaded, setSceneImageLoaded] = useState(false);

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

  // Reset image loaded state when image URL changes
  useEffect(() => {
    if (scene) {
      setSceneImageLoaded(false);
    }
  }, [scene?.generatedImage, scene?.sketchS3Url, scene]);

  // Early returns after all hooks
  if (!currentProject || !sceneId) {
    return (
      <div className="w-full bg-white h-full flex items-center justify-center">
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
    <div className="w-full h-full overflow-y-auto p-6">
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
            
            <div className="space-y-2">
              <FileUpload
                label="Upload Sketch/Image"
                accept="image/*"
                currentFile={scene.sketch}
                onChange={(file) => handleSceneChange('sketch', file)}
              />
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsExcalidrawOpen(true)}
                className="w-full"
                style={{
                  borderColor: '#5227FF',
                  color: '#5227FF',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#5227FF';
                  e.currentTarget.style.color = 'white';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = '#5227FF';
                }}
              >
                <Pencil className="w-4 h-4 mr-2" />
                Draw Sketch
              </Button>
            </div>
            
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
                <div className="relative rounded-lg border border-slate-200 overflow-hidden">
                  {/* Skeleton/Placeholder */}
                  {!sceneImageLoaded && (
                    <div className="absolute inset-0 bg-gradient-to-br from-slate-200 via-slate-100 to-slate-200 animate-pulse" />
                  )}
                  {/* Actual Image - Hidden until loaded */}
                  <img
                    src={scene.generatedImage}
                    alt="Scene"
                    className={`w-full rounded-lg transition-opacity duration-500 ${
                      sceneImageLoaded ? 'opacity-100 animate-fade-in-up' : 'opacity-0'
                    }`}
                    style={{
                      animationDelay: sceneImageLoaded ? '0ms' : '0ms',
                      animationFillMode: 'both',
                    }}
                    onLoad={() => setSceneImageLoaded(true)}
                  />
                </div>
              </div>
            )}
            
            {scene.sketchS3Url && !scene.generatedImage && (
              <div>
                <p className="text-xs text-slate-600 mb-2">Sketch</p>
                <div className="relative rounded-lg border border-slate-200 overflow-hidden">
                  {/* Skeleton/Placeholder */}
                  {!sceneImageLoaded && (
                    <div className="absolute inset-0 bg-gradient-to-br from-slate-200 via-slate-100 to-slate-200 animate-pulse" />
                  )}
                  {/* Actual Image - Hidden until loaded */}
                  <img
                    src={scene.sketchS3Url}
                    alt="Scene Sketch"
                    className={`w-full rounded-lg opacity-50 transition-opacity duration-500 ${
                      sceneImageLoaded ? 'opacity-50 animate-fade-in-up' : 'opacity-0'
                    }`}
                    style={{
                      animationDelay: sceneImageLoaded ? '0ms' : '0ms',
                      animationFillMode: 'both',
                    }}
                    onLoad={() => setSceneImageLoaded(true)}
                  />
                </div>
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
                style={{
                  borderColor: '#5227FF',
                  color: '#5227FF',
                }}
                onMouseEnter={(e) => {
                  if (!e.currentTarget.disabled) {
                    e.currentTarget.style.backgroundColor = '#5227FF';
                    e.currentTarget.style.color = 'white';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!e.currentTarget.disabled) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = '#5227FF';
                  }
                }}
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
            style={{
              backgroundColor: '#5227FF',
              color: 'white',
              border: 'none',
            }}
            onMouseEnter={(e) => {
              if (!e.currentTarget.disabled) {
                e.currentTarget.style.backgroundColor = '#4218E6';
              }
            }}
            onMouseLeave={(e) => {
              if (!e.currentTarget.disabled) {
                e.currentTarget.style.backgroundColor = '#5227FF';
              }
            }}
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

      {/* Excalidraw Modal */}
      <ExcalidrawModal
        isOpen={isExcalidrawOpen}
        onClose={() => setIsExcalidrawOpen(false)}
        onSave={(file) => {
          handleSceneChange('sketch', file);
          setIsExcalidrawOpen(false);
        }}
      />
    </div>
  );
};

