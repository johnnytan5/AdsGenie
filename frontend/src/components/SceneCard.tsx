'use client';

import { Scene } from '@/store/projectStore';
import { useProjectStore } from '@/store/projectStore';
import { Card } from './ui/Card';
import { Input } from './ui/Input';
import { Textarea } from './ui/Textarea';
import { FileUpload } from './ui/FileUpload';
import { Button } from './ui/Button';
import { GripVertical, Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import { useState, useEffect } from 'react';

interface SceneCardProps {
  scene: Scene;
  index: number;
  onUpdate: (updates: Partial<Scene>) => void;
  onDelete: () => void;
  isSelected?: boolean;
  onSelect?: () => void;
  dragAttributes?: any;
  dragListeners?: any;
}

export const SceneCard: React.FC<SceneCardProps> = ({
  scene,
  index,
  onUpdate,
  onDelete,
  isSelected = false,
  onSelect,
  dragAttributes,
  dragListeners,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);

  const { currentProject, generateSceneImage, setScene } = useProjectStore();

  // Reset loading state when image is generated or status changes
  useEffect(() => {
    if (scene.generatedImage && isGeneratingImage) {
      setIsGeneratingImage(false);
    }
    if (scene.status === 'done' || scene.status === 'failed') {
      setIsGeneratingImage(false);
    }
  }, [scene.generatedImage, scene.status, isGeneratingImage]);

  const handleSceneChange = (field: string, value: any) => {
    // Only update local state - no API calls
    setScene(scene.id, { [field]: value });
  };

  const handleGenerateImage = async () => {
    if (!currentProject) return;
    setIsGeneratingImage(true);
    try {
      await generateSceneImage(scene.id);
    } finally {
      // Keep loading state until webhook updates (or timeout)
      // The webhook will trigger a refresh which will show the generated image
      setTimeout(() => setIsGeneratingImage(false), 30000); // 30 second timeout
    }
  };

  return (
    <Card
      className={`p-5 ${isSelected ? 'ring-2 ring-blue-500 border-blue-500' : ''}`}
      onClick={onSelect}
    >
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className="cursor-grab active:cursor-grabbing"
              {...dragAttributes}
              {...dragListeners}
            >
              <GripVertical className="w-5 h-5 text-slate-400" />
            </div>
            <span className="text-sm font-medium text-slate-500">
              Scene {scene.order}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsExpanded(!isExpanded);
              }}
              className="p-1 hover:bg-slate-100 rounded"
            >
              {isExpanded ? (
                <ChevronUp className="w-4 h-4 text-slate-600" />
              ) : (
                <ChevronDown className="w-4 h-4 text-slate-600" />
              )}
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              className="p-1 hover:bg-red-50 rounded text-red-600"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Thumbnail */}
        <div className="aspect-video bg-slate-100 rounded-lg border border-slate-200 flex items-center justify-center overflow-hidden">
          {scene.generatedImage ? (
            <img
              src={scene.generatedImage}
              alt={`Scene ${scene.order}`}
              className="w-full h-full object-cover"
            />
          ) : scene.sketchS3Url ? (
            <img
              src={scene.sketchS3Url}
              alt={`Scene ${scene.order} sketch`}
              className="w-full h-full object-cover opacity-50"
            />
          ) : (
            <span className="text-slate-400 text-sm">No image</span>
          )}
        </div>

        {/* Collapsed View - shows only thumbnail and header, expand to edit */}

        {/* Expanded View */}
        {isExpanded && (
          <div className="space-y-4 pt-2 border-t border-slate-200">
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
              rows={3}
            />
            
            <FileUpload
              label="Upload Sketch/Image"
              accept="image/*"
              currentFile={scene.sketch}
              onChange={(file) => handleSceneChange('sketch', file)}
            />
            
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                handleGenerateImage();
              }}
              className="w-full"
              disabled={((!scene.imageDescription || scene.imageDescription.trim() === '') && !scene.sketch && !scene.sketchS3Url) || isGeneratingImage || scene.status === 'processing'}
              loading={isGeneratingImage || scene.status === 'processing'}
            >
              {(isGeneratingImage || scene.status === 'processing') ? 'Generating...' : 'Generate Image for Scene'}
            </Button>
            
            {(!scene.imageDescription || scene.imageDescription.trim() === '') && !scene.sketch && !scene.sketchS3Url && (
              <p className="text-xs text-slate-500 mt-1">Please provide an image description or upload a sketch to generate an image</p>
            )}
            
            {scene.status === 'failed' && (
              <p className="text-xs text-red-600">Generation failed. Please try again.</p>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}

