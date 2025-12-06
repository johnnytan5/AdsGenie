'use client';

import { useState, useEffect } from 'react';
import { useProjectStore } from '@/store/projectStore';
import { Input } from './ui/Input';
import { Textarea } from './ui/Textarea';
import { FileUpload } from './ui/FileUpload';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { ExcalidrawModal } from './ExcalidrawModal';
import { Pencil } from 'lucide-react';

export const GlobalSettingsPanel = () => {
  const { currentProject, setGlobalCharacter, setGlobalSetting, generateGlobalCharacterImage, generateGlobalSettingImage } = useProjectStore();
  const [isGeneratingCharacter, setIsGeneratingCharacter] = useState(false);
  const [isGeneratingSetting, setIsGeneratingSetting] = useState(false);
  const [isExcalidrawOpenCharacter, setIsExcalidrawOpenCharacter] = useState(false);
  const [isExcalidrawOpenSetting, setIsExcalidrawOpenSetting] = useState(false);
  const [characterImageLoaded, setCharacterImageLoaded] = useState(false);
  const [settingImageLoaded, setSettingImageLoaded] = useState(false);

  if (!currentProject) return null;

  const { character, setting } = currentProject.globalSettings;

  // Reset loading states when images are generated (webhook updates)
  useEffect(() => {
    if (character.image && isGeneratingCharacter) {
      setIsGeneratingCharacter(false);
    }
  }, [character.image, isGeneratingCharacter]);

  useEffect(() => {
    if (setting.image && isGeneratingSetting) {
      setIsGeneratingSetting(false);
    }
  }, [setting.image, isGeneratingSetting]);

  // Reset image loaded states when image URLs change
  useEffect(() => {
    setCharacterImageLoaded(false);
  }, [character.image, character.sketchS3Url]);

  useEffect(() => {
    setSettingImageLoaded(false);
  }, [setting.image, setting.sketchS3Url]);

  const handleCharacterChange = (field: string, value: string | File | null) => {
    // Only update local state - no API calls
    setGlobalCharacter({ [field]: value });
  };

  const handleSettingChange = (field: string, value: string | File | null) => {
    // Only update local state - no API calls
    setGlobalSetting({ [field]: value });
  };

  const handleGenerateCharacter = async () => {
    // This will save character data and trigger generation
    setIsGeneratingCharacter(true);
    try {
      await generateGlobalCharacterImage();
    } finally {
      // Keep loading state until webhook updates (or timeout)
      // The webhook will trigger a refresh which will show the generated image
      setTimeout(() => setIsGeneratingCharacter(false), 30000); // 30 second timeout
    }
  };

  const handleGenerateSetting = async () => {
    // This will save setting data and trigger generation
    setIsGeneratingSetting(true);
    try {
      await generateGlobalSettingImage();
    } finally {
      // Keep loading state until webhook updates (or timeout)
      setTimeout(() => setIsGeneratingSetting(false), 30000); // 30 second timeout
    }
  };

  return (
    <div className="w-full h-full overflow-y-auto p-6 space-y-8">
      <div>
        <h2 className="text-lg font-semibold text-slate-900 mb-6">Global Settings</h2>
      </div>

      {/* Global Character Section */}
      <Card className="p-5">
        <h3 className="text-base font-semibold text-slate-900 mb-4">Global Character</h3>
        <div className="space-y-4">
          <Input
            label="Character Name"
            value={character.name}
            onChange={(e) => handleCharacterChange('name', e.target.value)}
            placeholder="e.g., Friendly Mascot"
          />
          
          <Textarea
            label="Character Description"
            value={character.description}
            onChange={(e) => handleCharacterChange('description', e.target.value)}
            placeholder="Describe the character's appearance, style, and personality..."
            rows={4}
          />
          
          <div className="space-y-2">
            <FileUpload
              label="Upload Sketch/Image"
              accept="image/*"
              currentFile={character.sketch}
              onChange={(file) => handleCharacterChange('sketch', file)}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsExcalidrawOpenCharacter(true)}
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
          
          {character.image && (
            <div className="mt-2 relative rounded-lg border border-slate-200 overflow-hidden">
              {/* Skeleton/Placeholder */}
              {!characterImageLoaded && (
                <div className="absolute inset-0 bg-gradient-to-br from-slate-200 via-slate-100 to-slate-200 animate-pulse" />
              )}
              {/* Actual Image - Hidden until loaded */}
              <img
                src={character.image}
                alt="Character"
                className={`w-full rounded-lg transition-opacity duration-500 ${
                  characterImageLoaded ? 'opacity-100 animate-fade-in-up' : 'opacity-0'
                }`}
                style={{
                  animationDelay: characterImageLoaded ? '0ms' : '0ms',
                  animationFillMode: 'both',
                }}
                onLoad={() => setCharacterImageLoaded(true)}
              />
            </div>
          )}
          
          {character.sketchS3Url && !character.image && (
            <div className="mt-2 relative rounded-lg border border-slate-200 overflow-hidden">
              {/* Skeleton/Placeholder */}
              {!characterImageLoaded && (
                <div className="absolute inset-0 bg-gradient-to-br from-slate-200 via-slate-100 to-slate-200 animate-pulse" />
              )}
              {/* Actual Image - Hidden until loaded */}
              <img
                src={character.sketchS3Url}
                alt="Character Sketch"
                className={`w-full rounded-lg opacity-50 transition-opacity duration-500 ${
                  characterImageLoaded ? 'opacity-50 animate-fade-in-up' : 'opacity-0'
                }`}
                style={{
                  animationDelay: characterImageLoaded ? '0ms' : '0ms',
                  animationFillMode: 'both',
                }}
                onLoad={() => setCharacterImageLoaded(true)}
              />
              <p className="text-xs text-slate-500 mt-1">Sketch - Generating image...</p>
            </div>
          )}
          
          <Button
            variant="primary"
            size="sm"
            onClick={handleGenerateCharacter}
            className="w-full"
            disabled={(!character.description && !character.sketch && !character.sketchS3Url) || isGeneratingCharacter}
            loading={isGeneratingCharacter}
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
            {isGeneratingCharacter ? 'Generating...' : 'Generate Character Image'}
          </Button>
        </div>
      </Card>

      {/* Global Setting Section */}
      <Card className="p-5">
        <h3 className="text-base font-semibold text-slate-900 mb-4">Global Scene / Setting</h3>
        <div className="space-y-4">
          <Input
            label="Setting Name"
            value={setting.name}
            onChange={(e) => handleSettingChange('name', e.target.value)}
            placeholder="e.g., Modern Office"
          />
          
          <Textarea
            label="Setting Description"
            value={setting.description}
            onChange={(e) => handleSettingChange('description', e.target.value)}
            placeholder="Describe the location, atmosphere, and style..."
            rows={4}
          />
          
          <div className="space-y-2">
            <FileUpload
              label="Upload Sketch/Image"
              accept="image/*"
              currentFile={setting.sketch}
              onChange={(file) => handleSettingChange('sketch', file)}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsExcalidrawOpenSetting(true)}
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
          
          {setting.image && (
            <div className="mt-2 relative rounded-lg border border-slate-200 overflow-hidden">
              {/* Skeleton/Placeholder */}
              {!settingImageLoaded && (
                <div className="absolute inset-0 bg-gradient-to-br from-slate-200 via-slate-100 to-slate-200 animate-pulse" />
              )}
              {/* Actual Image - Hidden until loaded */}
              <img
                src={setting.image}
                alt="Setting"
                className={`w-full rounded-lg transition-opacity duration-500 ${
                  settingImageLoaded ? 'opacity-100 animate-fade-in-up' : 'opacity-0'
                }`}
                style={{
                  animationDelay: settingImageLoaded ? '100ms' : '0ms',
                  animationFillMode: 'both',
                }}
                onLoad={() => setSettingImageLoaded(true)}
              />
            </div>
          )}
          
          {setting.sketchS3Url && !setting.image && (
            <div className="mt-2 relative rounded-lg border border-slate-200 overflow-hidden">
              {/* Skeleton/Placeholder */}
              {!settingImageLoaded && (
                <div className="absolute inset-0 bg-gradient-to-br from-slate-200 via-slate-100 to-slate-200 animate-pulse" />
              )}
              {/* Actual Image - Hidden until loaded */}
              <img
                src={setting.sketchS3Url}
                alt="Setting Sketch"
                className={`w-full rounded-lg opacity-50 transition-opacity duration-500 ${
                  settingImageLoaded ? 'opacity-50 animate-fade-in-up' : 'opacity-0'
                }`}
                style={{
                  animationDelay: settingImageLoaded ? '100ms' : '0ms',
                  animationFillMode: 'both',
                }}
                onLoad={() => setSettingImageLoaded(true)}
              />
              <p className="text-xs text-slate-500 mt-1">Sketch - Generating image...</p>
            </div>
          )}
          
          <Button
            variant="primary"
            size="sm"
            onClick={handleGenerateSetting}
            className="w-full"
            disabled={(!setting.description && !setting.sketch && !setting.sketchS3Url) || isGeneratingSetting}
            loading={isGeneratingSetting}
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
            {isGeneratingSetting ? 'Generating...' : 'Generate Setting Image'}
          </Button>
        </div>
      </Card>

      {/* Excalidraw Modals */}
      <ExcalidrawModal
        isOpen={isExcalidrawOpenCharacter}
        onClose={() => setIsExcalidrawOpenCharacter(false)}
        onSave={(file) => {
          handleCharacterChange('sketch', file);
          setIsExcalidrawOpenCharacter(false);
        }}
      />
      <ExcalidrawModal
        isOpen={isExcalidrawOpenSetting}
        onClose={() => setIsExcalidrawOpenSetting(false)}
        onSave={(file) => {
          handleSettingChange('sketch', file);
          setIsExcalidrawOpenSetting(false);
        }}
      />
    </div>
  );
};

