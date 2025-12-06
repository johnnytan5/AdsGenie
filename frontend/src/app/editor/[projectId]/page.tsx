'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useProjectStore } from '@/store/projectStore';
import { GlobalSettingsPanel } from '@/components/GlobalSettingsPanel';
import { SceneList } from '@/components/SceneList';
import { SceneInspector } from '@/components/SceneInspector';
import { SceneTimeline } from '@/components/SceneTimeline';
import { VideoPreviewModal } from '@/components/VideoPreviewModal';
import { WebhookListener } from '@/components/WebhookListener';
import { UserJourney } from '@/components/UserJourney';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ArrowLeft, Plus, Play, Save, ChevronUp, ChevronDown, Eye } from 'lucide-react';

export default function EditorPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params?.projectId as string | undefined;
  
  const { currentProject, addScene, saveProject, setCurrentProject, loadProject, isLoading, generateFullVideo, refreshProject } = useProjectStore();
  const [selectedSceneId, setSelectedSceneId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isEditingName, setIsEditingName] = useState(false);
  const [editingNameValue, setEditingNameValue] = useState<string>('');
  const [generatedVideoUrl, setGeneratedVideoUrl] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isTimelineVisible, setIsTimelineVisible] = useState(true);
  const [isLoadingProject, setIsLoadingProject] = useState(true);

  // Load project from URL parameter on mount
  useEffect(() => {
    if (projectId) {
      loadProject(projectId)
        .then(() => {
          setIsLoadingProject(false);
        })
        .catch((error) => {
          console.error('Failed to load project:', error);
          // If project not found, redirect to projects page
          router.push('/projects');
        });
    } else {
      // No projectId in URL, redirect to aspect-ratio to create new project
      router.push('/aspect-ratio');
    }
  }, [projectId, loadProject, router]);

  // Update URL when project changes (but don't reload)
  useEffect(() => {
    if (currentProject && currentProject.id !== projectId) {
      // Update URL without reloading
      window.history.replaceState(null, '', `/editor/${currentProject.id}`);
    }
  }, [currentProject, projectId]);

  const handleGenerateVideo = async () => {
    if (!currentProject) return;
    
    setIsGenerating(true);
    try {
      await generateFullVideo();
      // Webhook will trigger refreshProject, which will update currentProject
      // The useEffect below will detect the finalVideoS3Url change and show the modal
    } catch (error) {
      console.error('Failed to generate video:', error);
      setIsGenerating(false);
    }
  };

  // Watch for final video URL changes and show modal
  useEffect(() => {
    if (currentProject?.finalVideoS3Url && isGenerating) {
      // Final video is ready, show modal
      setGeneratedVideoUrl(currentProject.finalVideoS3Url);
      setIsModalOpen(true);
      setIsGenerating(false);
    }
    // If final video was cleared (empty string or null) and we're generating, keep generating state
    if (!currentProject?.finalVideoS3Url && isGenerating) {
      // Video was cleared, continue generating
      console.log('[Editor] Final video cleared, continuing generation...');
    }
  }, [currentProject?.finalVideoS3Url, isGenerating]);

  const handleModalSave = () => {
    saveProject();
    // TODO: Show success toast
  };

  const handleModalExport = () => {
    // Export functionality is handled in the modal component
    // TODO: Add any additional export logic here
  };

  const handleBackToEditing = () => {
    setIsModalOpen(false);
  };

  const handleViewFullVideo = () => {
    if (currentProject?.finalVideoS3Url) {
      setGeneratedVideoUrl(currentProject.finalVideoS3Url);
      setIsModalOpen(true);
    }
  };

  const handleSave = async () => {
    await saveProject();
    // TODO: Show success toast
  };

  if (isLoadingProject || !currentProject) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-slate-400">Loading project...</p>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-slate-50">
      <WebhookListener />
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push('/projects')}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div className="flex items-center gap-3">
            {isEditingName ? (
              <Input
                value={editingNameValue}
                onChange={(e) => {
                  setEditingNameValue(e.target.value);
                }}
                onBlur={async () => {
                  setIsEditingName(false);
                  const newName = editingNameValue.trim();
                  if (newName && currentProject && newName !== currentProject.name) {
                    await saveProject(newName);
                  } else {
                    // Reset to current project name if cancelled
                    setEditingNameValue(currentProject.name);
                  }
                }}
                onKeyDown={async (e) => {
                  if (e.key === 'Enter') {
                    setIsEditingName(false);
                    const newName = editingNameValue.trim();
                    if (newName && currentProject && newName !== currentProject.name) {
                      await saveProject(newName);
                    } else {
                      setEditingNameValue(currentProject.name);
                    }
                  } else if (e.key === 'Escape') {
                    setIsEditingName(false);
                    setEditingNameValue(currentProject.name);
                  }
                }}
                className="w-64"
                autoFocus
              />
            ) : (
              <div>
                <h1
                  className="text-lg font-semibold text-slate-900 cursor-pointer hover:text-blue-600"
                  onClick={() => {
                    setEditingNameValue(currentProject.name);
                    setIsEditingName(true);
                  }}
                >
                  {currentProject.name}
                </h1>
                <p className="text-xs text-slate-500">
                  {currentProject.aspectRatio} • {currentProject.scenes.length} scenes
                </p>
              </div>
            )}
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleSave}
        >
          <Save className="w-4 h-4 mr-2" />
          Save Project
        </Button>
      </header>

      {/* User Journey Progress */}
      <UserJourney />

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Global Settings */}
        <GlobalSettingsPanel />

        {/* Center - Timeline */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto">
            <SceneList
              selectedSceneId={selectedSceneId}
              onSelectScene={setSelectedSceneId}
            />
          </div>
        </div>

        {/* Right Sidebar - Scene Inspector */}
        <SceneInspector sceneId={selectedSceneId} />
      </div>

      {/* Bottom Bar */}
      <div className="bg-white border-t border-slate-200 flex flex-col">
        {/* Scene Timeline */}
        {isTimelineVisible && (
          <div className="px-6 py-3 border-b border-slate-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-slate-600">Timeline</span>
              <button
                onClick={() => setIsTimelineVisible(false)}
                className="p-1 hover:bg-slate-100 rounded transition-colors"
                title="Hide timeline"
                type="button"
              >
                <ChevronDown className="w-4 h-4 text-slate-600" />
              </button>
            </div>
            <SceneTimeline
              selectedSceneId={selectedSceneId}
              onSelectScene={setSelectedSceneId}
            />
          </div>
        )}
        
        {/* Action Buttons */}
        <div className="px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsTimelineVisible(!isTimelineVisible)}
              className={`flex items-center gap-1.5 px-3 py-2 hover:bg-slate-100 rounded transition-colors border border-slate-200 text-sm font-medium ${!isTimelineVisible ? 'bg-slate-50 border-slate-300 text-slate-700' : 'text-slate-600'}`}
              title={isTimelineVisible ? "Hide timeline" : "Show timeline"}
              type="button"
              aria-label={isTimelineVisible ? "Hide timeline" : "Show timeline"}
            >
              {isTimelineVisible ? (
                <>
                  <ChevronDown className="w-4 h-4" />
                  <span>Hide Timeline</span>
                </>
              ) : (
                <>
                  <ChevronUp className="w-4 h-4" />
                  <span>Show Timeline</span>
                </>
              )}
            </button>
            <Button
              variant="outline"
              onClick={() => addScene()}
            >
              <Plus className="w-4 h-4 mr-2" />
              Add New Scene
            </Button>
          </div>
          <div className="flex items-center gap-3">
            {currentProject.finalVideoS3Url && currentProject.finalVideoS3Url.trim() !== '' && (
              <Button
                variant="outline"
                onClick={handleViewFullVideo}
              >
                <Eye className="w-4 h-4 mr-2" />
                View Full Video
              </Button>
            )}
            <Button
              variant="primary"
              onClick={handleGenerateVideo}
              disabled={isGenerating || currentProject.scenes.length === 0}
            >
              <Play className="w-4 h-4 mr-2" />
              {isGenerating ? 'Generating...' : 'Generate Full Video'}
            </Button>
          </div>
        </div>
      </div>

      {/* Video Preview Modal */}
      <VideoPreviewModal
        videoUrl={generatedVideoUrl}
        isOpen={isModalOpen}
        onClose={handleBackToEditing}
        onSave={handleModalSave}
        onExport={handleModalExport}
        onBackToEditing={handleBackToEditing}
        projectId={currentProject?.id}
      />
    </div>
  );
}

