'use client';

import { useState, useEffect } from 'react';
import { useProjectStore } from '@/store/projectStore';
import { Input } from './ui/Input';
import { Textarea } from './ui/Textarea';
import { FileUpload } from './ui/FileUpload';
import { Button } from './ui/Button';
import { Card } from './ui/Card';

export const GlobalSettingsPanel = () => {
  const { currentProject, setGlobalCharacter, setGlobalSetting, generateGlobalCharacterImage, generateGlobalSettingImage } = useProjectStore();
  const [isGeneratingCharacter, setIsGeneratingCharacter] = useState(false);
  const [isGeneratingSetting, setIsGeneratingSetting] = useState(false);

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
    <div className="w-80 bg-white border-r border-slate-200 h-full overflow-y-auto p-6 space-y-8">
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
          
          <FileUpload
            label="Upload Sketch/Image"
            accept="image/*"
            currentFile={character.sketch}
            onChange={(file) => handleCharacterChange('sketch', file)}
          />
          
          {character.image && (
            <div className="mt-2">
              <img
                src={character.image}
                alt="Character"
                className="w-full rounded-lg border border-slate-200"
              />
            </div>
          )}
          
          {character.sketchS3Url && !character.image && (
            <div className="mt-2">
              <img
                src={character.sketchS3Url}
                alt="Character Sketch"
                className="w-full rounded-lg border border-slate-200 opacity-50"
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
          
          <FileUpload
            label="Upload Sketch/Image"
            accept="image/*"
            currentFile={setting.sketch}
            onChange={(file) => handleSettingChange('sketch', file)}
          />
          
          {setting.image && (
            <div className="mt-2">
              <img
                src={setting.image}
                alt="Setting"
                className="w-full rounded-lg border border-slate-200"
              />
            </div>
          )}
          
          {setting.sketchS3Url && !setting.image && (
            <div className="mt-2">
              <img
                src={setting.sketchS3Url}
                alt="Setting Sketch"
                className="w-full rounded-lg border border-slate-200 opacity-50"
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
          >
            {isGeneratingSetting ? 'Generating...' : 'Generate Setting Image'}
          </Button>
        </div>
      </Card>
    </div>
  );
};

