'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useProjectStore } from '@/store/projectStore';
import { GlobalSettingsPanel } from '@/components/GlobalSettingsPanel';
import { SceneList } from '@/components/SceneList';
import { SceneInspector } from '@/components/SceneInspector';
import { SceneTimeline } from '@/components/SceneTimeline';
import { VideoPreviewModal } from '@/components/VideoPreviewModal';
import { WebhookListener } from '@/components/WebhookListener';
import { UserJourney } from '@/components/UserJourney';
import CursorGenie from '@/components/CursorGenie';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ArrowLeft, Plus, Play, Save, ChevronUp, ChevronDown, Eye, ChevronLeft, ChevronRight, GripVertical } from 'lucide-react';

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
  const [isTimelineVisible, setIsTimelineVisible] = useState(false); // Hidden by default
  const [isLoadingProject, setIsLoadingProject] = useState(true);
  const [isGlobalSettingsCollapsed, setIsGlobalSettingsCollapsed] = useState(false);
  const [globalSettingsWidth, setGlobalSettingsWidth] = useState(() => {
    // Default to ~1/3 of viewport width, with min 400px and max 800px
    if (typeof window !== 'undefined') {
      return Math.max(400, Math.min(800, Math.floor(window.innerWidth / 3)));
    }
    return 640; // Fallback for SSR
  });
  const [isResizing, setIsResizing] = useState(false);
  const resizeStartX = useRef<number>(0);
  const resizeStartWidth = useRef<number>(640);
  
  const [isSceneInspectorCollapsed, setIsSceneInspectorCollapsed] = useState(true); // Hidden by default
  const [sceneInspectorWidth, setSceneInspectorWidth] = useState(() => {
    // Default to 40% of viewport width, with min 300px and max 700px
    if (typeof window !== 'undefined') {
      return Math.max(300, Math.min(700, Math.floor(window.innerWidth * 0.4)));
    }
    return 500; // Fallback for SSR
  });
  const [isResizingInspector, setIsResizingInspector] = useState(false);
  const resizeInspectorStartX = useRef<number>(0);
  const resizeInspectorStartWidth = useRef<number>(500);

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

  // Listen for final video ready event from webhook
  useEffect(() => {
    const handleFinalVideoReady = (event: CustomEvent) => {
      const { presignedUrl } = event.detail;
      console.log('[Editor] Final video ready event received', presignedUrl);
      if (presignedUrl) {
        setGeneratedVideoUrl(presignedUrl);
        setIsModalOpen(true);
        setIsGenerating(false);
        // Also refresh project to update the store
        refreshProject();
      }
    };

    window.addEventListener('final-video-ready', handleFinalVideoReady as EventListener);
    return () => {
      window.removeEventListener('final-video-ready', handleFinalVideoReady as EventListener);
    };
  }, [refreshProject]);


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

  // Global Settings resize handlers
  const handleResizeMove = useCallback((e: MouseEvent) => {
    const diff = e.clientX - resizeStartX.current; // Positive when dragging right, negative when dragging left
    const newWidth = Math.max(200, Math.min(600, resizeStartWidth.current + diff));
    setGlobalSettingsWidth(newWidth);
  }, []);

  const handleResizeEnd = useCallback(() => {
    setIsResizing(false);
    document.removeEventListener('mousemove', handleResizeMove);
    document.removeEventListener('mouseup', handleResizeEnd);
  }, [handleResizeMove]);

  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
    resizeStartX.current = e.clientX;
    resizeStartWidth.current = globalSettingsWidth;
    document.addEventListener('mousemove', handleResizeMove);
    document.addEventListener('mouseup', handleResizeEnd);
  }, [globalSettingsWidth, handleResizeMove, handleResizeEnd]);

  // Initialize resizeStartWidth ref when component mounts or width changes
  useEffect(() => {
    resizeStartWidth.current = globalSettingsWidth;
  }, [globalSettingsWidth]);

  // Scene Inspector resize handlers
  const handleInspectorResizeMove = useCallback((e: MouseEvent) => {
    const diff = resizeInspectorStartX.current - e.clientX; // Positive when dragging left, negative when dragging right
    const newWidth = Math.max(300, Math.min(700, resizeInspectorStartWidth.current + diff));
    setSceneInspectorWidth(newWidth);
  }, []);

  const handleInspectorResizeEnd = useCallback(() => {
    setIsResizingInspector(false);
    document.removeEventListener('mousemove', handleInspectorResizeMove);
    document.removeEventListener('mouseup', handleInspectorResizeEnd);
  }, [handleInspectorResizeMove]);

  const handleInspectorResizeStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizingInspector(true);
    resizeInspectorStartX.current = e.clientX;
    resizeInspectorStartWidth.current = sceneInspectorWidth;
    document.addEventListener('mousemove', handleInspectorResizeMove);
    document.addEventListener('mouseup', handleInspectorResizeEnd);
  }, [sceneInspectorWidth, handleInspectorResizeMove, handleInspectorResizeEnd]);

  // Initialize resizeInspectorStartWidth ref when component mounts or width changes
  useEffect(() => {
    resizeInspectorStartWidth.current = sceneInspectorWidth;
  }, [sceneInspectorWidth]);

  // Show Scene Inspector when a scene is selected
  useEffect(() => {
    if (selectedSceneId) {
      setIsSceneInspectorCollapsed(false);
    }
  }, [selectedSceneId]);

  useEffect(() => {
    return () => {
      document.removeEventListener('mousemove', handleResizeMove);
      document.removeEventListener('mouseup', handleResizeEnd);
      document.removeEventListener('mousemove', handleInspectorResizeMove);
      document.removeEventListener('mouseup', handleInspectorResizeEnd);
    };
  }, [handleResizeMove, handleResizeEnd, handleInspectorResizeMove, handleInspectorResizeEnd]);

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
      <CursorGenie size={80} />
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push('/projects')}
            style={{
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
                  className="text-lg font-semibold text-slate-900 cursor-pointer hover:text-purple-600"
                  style={{
                    '--hover-color': '#5227FF',
                  } as React.CSSProperties}
                  onClick={() => {
                    setEditingNameValue(currentProject.name);
                    setIsEditingName(true);
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.color = '#5227FF';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.color = '';
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
          <Save className="w-4 h-4 mr-2" />
          Save Project
        </Button>
      </header>

      {/* User Journey Progress */}
      <UserJourney />

      {/* Main Content */}
      <div 
        className="flex-1 flex overflow-hidden relative"
        style={{ userSelect: (isResizing || isResizingInspector) ? 'none' : 'auto' }}
      >
        {/* Left Sidebar - Global Settings */}
        <div
          className={`bg-white border-r border-slate-200 h-full flex ${
            isGlobalSettingsCollapsed ? '' : 'transition-all duration-300'
          }`}
          style={{
            width: isGlobalSettingsCollapsed ? 0 : `${globalSettingsWidth}px`,
            minWidth: isGlobalSettingsCollapsed ? 0 : `${globalSettingsWidth}px`,
            transition: isResizing ? 'none' : 'width 300ms, min-width 300ms',
          }}
        >
          <div className="flex-1 overflow-y-auto">
            <GlobalSettingsPanel />
          </div>
          
          {/* Resize Handle */}
          {!isGlobalSettingsCollapsed && (
            <div
              className="w-1 bg-slate-200 hover:bg-slate-300 cursor-col-resize transition-colors flex-shrink-0 relative group"
              onMouseDown={handleResizeStart}
              style={{ cursor: isResizing ? 'col-resize' : 'col-resize' }}
            >
              <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 w-4 flex items-center justify-center">
                <GripVertical className="w-3 h-3 text-slate-400 group-hover:text-slate-600 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </div>
          )}
        </div>

        {/* Toggle Button - Always visible when collapsed */}
        {isGlobalSettingsCollapsed && (
          <button
            onClick={() => setIsGlobalSettingsCollapsed(false)}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-20 bg-white border-r border-t border-b border-slate-200 rounded-r-lg px-2 py-4 shadow-sm hover:bg-slate-50 transition-colors"
            title="Show Global Settings"
          >
            <ChevronRight className="w-4 h-4 text-slate-600" />
          </button>
        )}

        {/* Toggle Button - Visible when expanded */}
        {!isGlobalSettingsCollapsed && (
          <button
            onClick={() => setIsGlobalSettingsCollapsed(true)}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-20 bg-white border-r border-t border-b border-slate-200 rounded-r-lg px-2 py-4 shadow-sm hover:bg-slate-50 transition-colors"
            style={{ left: `${globalSettingsWidth}px` }}
            title="Hide Global Settings"
          >
            <ChevronLeft className="w-4 h-4 text-slate-600" />
          </button>
        )}

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
        <div
          className={`bg-white border-l border-slate-200 h-full flex ${
            isSceneInspectorCollapsed ? '' : 'transition-all duration-300'
          }`}
          style={{
            width: isSceneInspectorCollapsed ? 0 : `${sceneInspectorWidth}px`,
            minWidth: isSceneInspectorCollapsed ? 0 : `${sceneInspectorWidth}px`,
            transition: isResizingInspector ? 'none' : 'width 300ms, min-width 300ms',
          }}
        >
          {/* Resize Handle */}
          {!isSceneInspectorCollapsed && (
            <div
              className="w-1 bg-slate-200 hover:bg-slate-300 cursor-col-resize transition-colors flex-shrink-0 relative group"
              onMouseDown={handleInspectorResizeStart}
              style={{ cursor: isResizingInspector ? 'col-resize' : 'col-resize' }}
            >
              <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 w-4 flex items-center justify-center">
                <GripVertical className="w-3 h-3 text-slate-400 group-hover:text-slate-600 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </div>
          )}
          
          <div className="flex-1 overflow-y-auto">
            <SceneInspector sceneId={selectedSceneId} />
          </div>
        </div>

        {/* Toggle Button for Scene Inspector - Always visible when collapsed */}
        {isSceneInspectorCollapsed && (
          <button
            onClick={() => setIsSceneInspectorCollapsed(false)}
            className="absolute right-0 top-1/2 -translate-y-1/2 z-20 bg-white border-l border-t border-b border-slate-200 rounded-l-lg px-2 py-4 shadow-sm hover:bg-slate-50 transition-colors"
            title="Show Scene Inspector"
          >
            <ChevronLeft className="w-4 h-4 text-slate-600" />
          </button>
        )}

        {/* Toggle Button for Scene Inspector - Visible when expanded */}
        {!isSceneInspectorCollapsed && (
          <button
            onClick={() => setIsSceneInspectorCollapsed(true)}
            className="absolute right-0 top-1/2 -translate-y-1/2 z-20 bg-white border-l border-t border-b border-slate-200 rounded-l-lg px-2 py-4 shadow-sm hover:bg-slate-50 transition-colors"
            style={{ right: `${sceneInspectorWidth}px` }}
            title="Hide Scene Inspector"
          >
            <ChevronRight className="w-4 h-4 text-slate-600" />
          </button>
        )}
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
              className={`flex items-center gap-1.5 px-3 py-2 rounded transition-colors border text-sm font-medium ${
                !isTimelineVisible 
                  ? 'bg-purple-50 border-purple-300 text-purple-700 hover:bg-purple-100' 
                  : 'border-purple-200 text-purple-600 hover:bg-purple-50'
              }`}
              style={{
                borderColor: !isTimelineVisible ? '#5227FF' : '#5227FF',
              }}
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
              <Plus className="w-4 h-4 mr-2" />
              Add New Scene
            </Button>
          </div>
          <div className="flex items-center gap-3">
            {currentProject.finalVideoS3Url && currentProject.finalVideoS3Url.trim() !== '' && (
              <Button
                variant="outline"
                onClick={handleViewFullVideo}
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
                <Eye className="w-4 h-4 mr-2" />
                View Full Video
              </Button>
            )}
            <Button
              variant="primary"
              onClick={handleGenerateVideo}
              disabled={isGenerating || currentProject.scenes.length === 0}
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
        onExport={handleModalExport}
        onBackToEditing={handleBackToEditing}
        projectId={currentProject?.id}
      />
    </div>
  );
}

