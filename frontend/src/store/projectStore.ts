import { create } from 'zustand';
import { projectApi, sceneApi, globalSettingsApi, generationApi, ApiError } from '@/lib/api';

export type AspectRatio = '16:9' | '9:16';

export interface GlobalCharacter {
  name: string;
  description: string;
  sketch: File | null;
  image: string | null;
  sketchS3Url?: string | null;
}

export interface GlobalSetting {
  name: string;
  description: string;
  sketch: File | null;
  image: string | null;
  sketchS3Url?: string | null;
}

export interface GlobalSettings {
  character: GlobalCharacter;
  setting: GlobalSetting;
}

export interface Scene {
  id: string;
  order: number;
  duration: number;
  description: string;
  imageDescription: string;
  sketch: File | null;
  generatedImage: string | null;
  generatedVideo: string | null;
  sketchS3Url?: string | null;
  status?: 'pending' | 'processing' | 'done' | 'failed';
  // Audio settings
  voiceoverEnabled?: boolean;
  voiceoverText?: string;
  voiceoverGender?: 'male' | 'female';
  backgroundMusicEnabled?: boolean;
  // Image generation settings
  useGlobalCharacterForImage?: boolean;
  useGlobalSettingForImage?: boolean;
  // Video generation settings
  useGlobalCharacterForVideo?: boolean;
  useGlobalSettingForVideo?: boolean;
}

export interface Project {
  id: string;
  name: string;
  aspectRatio: AspectRatio;
  globalSettings: GlobalSettings;
  scenes: Scene[];
  updatedAt: Date;
  thumbnail: string | null;
  finalVideoS3Url?: string | null;
}

interface ProjectState {
  currentProject: Project | null;
  aspectRatio: AspectRatio | null;
  projects: Project[];
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setAspectRatio: (ratio: AspectRatio) => Promise<void>;
  createProject: (name: string, aspectRatio: AspectRatio) => Promise<Project>;
  setGlobalCharacter: (character: Partial<GlobalCharacter>) => void;
  setGlobalSetting: (setting: Partial<GlobalSetting>) => void;
  addScene: (description?: string, duration?: number, sketchFile?: File) => Promise<void>;
  setScene: (sceneId: string, updates: Partial<Scene>) => void;
  updateScene: (id: string, updates: Partial<Scene>) => Promise<void>;
  deleteScene: (id: string) => Promise<void>;
  reorderScenes: (startIndex: number, endIndex: number) => Promise<void>;
  setCurrentProject: (project: Project | null) => void;
  saveProject: (name?: string) => Promise<void>;
  loadProject: (id: string) => Promise<void>;
  loadProjects: () => Promise<void>;
  deleteProject: (id: string) => Promise<void>;
  generateSceneImage: (sceneId: string) => Promise<void>;
  generateSceneVideo: (sceneId: string, aspectRatio?: string, voiceoverText?: string) => Promise<void>;
  generateFullVideo: () => Promise<string | null>;
  generateGlobalCharacterImage: () => Promise<void>;
  generateGlobalSettingImage: () => Promise<void>;
  refreshProject: () => Promise<void>;
  refreshGlobalCharacter: () => Promise<void>;
  refreshGlobalSetting: () => Promise<void>;
  refreshScene: (sceneId: string, presignedUrl?: string) => Promise<void>;
}

// Webhook handler - called when backend sends webhook notification
function handleWebhookUpdate(projectId: string, taskType: string) {
  const store = useProjectStore.getState();
  // Only refresh if this is the current project
  if (store.currentProject && store.currentProject.id === projectId) {
    store.refreshProject().catch(console.error);
  }
}

// Helper to convert backend project to frontend project
function backendToFrontendProject(backendProject: any): Project {
  return {
    id: backendProject.project_id,
    name: backendProject.name,
    aspectRatio: backendProject.aspect_ratio as AspectRatio,
  globalSettings: {
    character: {
        name: backendProject.global_character?.name || '',
        description: backendProject.global_character?.description || '',
      sketch: null,
        image: backendProject.global_character?.generated_image_s3_url || null,
        sketchS3Url: backendProject.global_character?.sketch_s3_url || null,
    },
    setting: {
        name: backendProject.global_setting?.name || '',
        description: backendProject.global_setting?.description || '',
        sketch: null,
        image: backendProject.global_setting?.generated_image_s3_url || null,
        sketchS3Url: backendProject.global_setting?.sketch_s3_url || null,
      },
    },
    scenes: (backendProject.scenes || []).map((scene: any) => ({
      id: scene.scene_id,
      order: scene.order,
      duration: scene.duration,
      description: scene.description,
      imageDescription: scene.image_description || '',  // Use image_description field (separate from description)
      sketch: null,
      generatedImage: scene.generated_image_s3_url || null,
      generatedVideo: scene.generated_video_s3_url || null,
      sketchS3Url: scene.sketch_s3_url || null,
      status: scene.status || 'pending',
      voiceoverEnabled: scene.voiceover_enabled || false,
      voiceoverText: scene.voiceover_text || '',
      voiceoverGender: scene.voiceover_gender || 'male',
      backgroundMusicEnabled: scene.background_music_enabled || false,
      useGlobalCharacterForImage: scene.use_global_character_for_image || false,
      useGlobalSettingForImage: scene.use_global_setting_for_image || false,
      useGlobalCharacterForVideo: scene.use_global_character_for_video || false,
      useGlobalSettingForVideo: scene.use_global_setting_for_video || false,
    })),
    updatedAt: new Date(backendProject.updated_at),
    thumbnail: backendProject.scenes?.[0]?.generated_image_s3_url || null,
    finalVideoS3Url: backendProject.final_video_s3_url || null,
  };
}

// Export webhook handler for use in API routes or client-side
export { handleWebhookUpdate };

export const useProjectStore = create<ProjectState>((set, get) => ({
  currentProject: null,
  aspectRatio: null,
  projects: [],
  isLoading: false,
  error: null,
  
  setAspectRatio: async (ratio) => {
    set({ aspectRatio: ratio });
  },
  
  createProject: async (name, aspectRatio) => {
    try {
      set({ isLoading: true, error: null });
      const response = await projectApi.create(name, aspectRatio);
      const project: Project = {
        id: response.project_id,
        name: response.name,
        aspectRatio: response.aspect_ratio as AspectRatio,
        globalSettings: {
          character: { name: '', description: '', sketch: null, image: null },
          setting: { name: '', description: '', sketch: null, image: null },
        },
        scenes: [],
        updatedAt: new Date(),
        thumbnail: null,
      };
      set({ currentProject: project, aspectRatio: aspectRatio, isLoading: false });
      return project; // Return project so caller can get the ID
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Failed to create project';
      set({ error: message, isLoading: false });
      throw error;
    }
  },
  
  setGlobalCharacter: (character) => {
    const { currentProject } = get();
    if (!currentProject) return;

    // Only update local state synchronously
    const updatedProject = {
          ...currentProject,
          globalSettings: {
            ...currentProject.globalSettings,
            character: {
              ...currentProject.globalSettings.character,
              ...character,
            },
          },
    };
    set({ currentProject: updatedProject });
  },
  
  setGlobalSetting: (setting) => {
    const { currentProject } = get();
    if (!currentProject) return;

    // Only update local state synchronously
    const updatedProject = {
          ...currentProject,
          globalSettings: {
            ...currentProject.globalSettings,
            setting: {
              ...currentProject.globalSettings.setting,
              ...setting,
            },
          },
    };
    set({ currentProject: updatedProject });
  },

  addScene: async (description = 'New Scene', duration = 5, sketchFile) => {
    const { currentProject } = get();
    if (!currentProject) return;

    try {
      set({ isLoading: true, error: null });
      const response = await sceneApi.add(currentProject.id, description, duration, sketchFile);
      
      // Refresh project to get the new scene
      await get().refreshProject();
      set({ isLoading: false });
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Failed to add scene';
      set({ error: message, isLoading: false });
      throw error; // Re-throw so UI can handle it
    }
  },

  setScene: (sceneId, updates) => {
    const { currentProject } = get();
    if (!currentProject) return;

    // Only update local state - no API calls
    const updatedProject = {
      ...currentProject,
      scenes: currentProject.scenes.map((scene) =>
        scene.id === sceneId ? { ...scene, ...updates } : scene
      ),
      };
    set({ currentProject: updatedProject });
  },
  
  updateScene: async (id, updates) => {
    const { currentProject } = get();
    if (!currentProject) return;

    try {
      set({ isLoading: true, error: null });
      
      // Update local state first
      const updatedProject = {
          ...currentProject,
          scenes: currentProject.scenes.map((scene) =>
            scene.id === id ? { ...scene, ...updates } : scene
          ),
      };
      set({ currentProject: updatedProject });

      // Sync with backend
      const scene = updatedProject.scenes.find(s => s.id === id);
      if (scene) {
        await sceneApi.update(
          currentProject.id,
          id,
          updates.description !== undefined ? updates.description : scene.description,
          updates.duration !== undefined ? updates.duration : scene.duration,
          updates.sketch || undefined,
          updates.imageDescription !== undefined ? updates.imageDescription : (scene.imageDescription || ''),
          updates.voiceoverEnabled !== undefined ? updates.voiceoverEnabled : scene.voiceoverEnabled,
          updates.voiceoverText !== undefined ? updates.voiceoverText : scene.voiceoverText,
          updates.voiceoverGender !== undefined ? updates.voiceoverGender : scene.voiceoverGender,
          updates.backgroundMusicEnabled !== undefined ? updates.backgroundMusicEnabled : scene.backgroundMusicEnabled,
          updates.useGlobalCharacterForImage !== undefined ? updates.useGlobalCharacterForImage : scene.useGlobalCharacterForImage,
          updates.useGlobalSettingForImage !== undefined ? updates.useGlobalSettingForImage : scene.useGlobalSettingForImage,
          updates.useGlobalCharacterForVideo !== undefined ? updates.useGlobalCharacterForVideo : scene.useGlobalCharacterForVideo,
          updates.useGlobalSettingForVideo !== undefined ? updates.useGlobalSettingForVideo : scene.useGlobalSettingForVideo
        );
      }

      // Refresh project
      await get().refreshProject();
      set({ isLoading: false });
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Failed to update scene';
      set({ error: message, isLoading: false });
    }
  },
  
  deleteScene: async (id) => {
    const { currentProject } = get();
    if (!currentProject) return;

    try {
      set({ isLoading: true, error: null });
      await sceneApi.delete(currentProject.id, id);
      
      // Refresh project
      await get().refreshProject();
      set({ isLoading: false });
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Failed to delete scene';
      set({ error: message, isLoading: false });
    }
  },
  
  reorderScenes: async (startIndex, endIndex) => {
    const { currentProject } = get();
    if (!currentProject) return;

    try {
      set({ isLoading: true, error: null });
      
      // Update local state first
      const scenes = [...currentProject.scenes];
      const [removed] = scenes.splice(startIndex, 1);
      scenes.splice(endIndex, 0, removed);
      const reorderedScenes = scenes.map((scene, index) => ({
        ...scene,
        order: index + 1,
      }));
      
      const updatedProject = {
          ...currentProject,
          scenes: reorderedScenes,
      };
      set({ currentProject: updatedProject });

      // Sync with backend
      const sceneOrder = reorderedScenes.map((scene, index) => ({
        scene_id: scene.id,
        order: index + 1,
      }));
      await sceneApi.reorder(currentProject.id, sceneOrder);
      
      set({ isLoading: false });
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Failed to reorder scenes';
      set({ error: message, isLoading: false });
    }
  },
  
  setCurrentProject: (project) => {
    set({ currentProject: project });
    if (project) {
      set({ aspectRatio: project.aspectRatio });
    }
  },
  
  saveProject: async (name) => {
    const { currentProject } = get();
    if (!currentProject) return;

    try {
      // Don't set isLoading for name updates to avoid triggering WebhookListener polling
      // Only update project name if provided and different
      if (name && name !== currentProject.name) {
        // Update in backend first
        const updatedProject = await projectApi.update(currentProject.id, name);
        const frontendProject = backendToFrontendProject(updatedProject);
        // Update local state with the response from backend (which has the new name)
        set({ currentProject: frontendProject, error: null });
      }
      // If no name change, don't do anything (no need to refresh)
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Failed to save project';
      set({ error: message });
      console.error('Failed to save project name:', error);
    }
  },
  
  loadProject: async (id) => {
    try {
      set({ isLoading: true, error: null });
      const backendProject = await projectApi.get(id);
      const project = backendToFrontendProject(backendProject);
      set({ currentProject: project, aspectRatio: project.aspectRatio, isLoading: false });
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Failed to load project';
      set({ error: message, isLoading: false });
      throw error;
    }
  },
  
  loadProjects: async () => {
    try {
      set({ isLoading: true, error: null });
      const backendProjects = await projectApi.list();
      
      // Load full details for each project
      const projects = await Promise.all(
        backendProjects.map(async (p) => {
          try {
            const fullProject = await projectApi.get(p.project_id);
            return backendToFrontendProject(fullProject);
          } catch {
            // If loading full project fails, return minimal project
            return {
              id: p.project_id,
              name: p.name,
              aspectRatio: '16:9' as AspectRatio,
              globalSettings: {
                character: { name: '', description: '', sketch: null, image: null },
                setting: { name: '', description: '', sketch: null, image: null },
              },
              scenes: [],
              updatedAt: new Date(p.updated_at),
              thumbnail: p.thumbnail_s3_url || null,
            };
          }
        })
      );
      
      set({ projects, isLoading: false });
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Failed to load projects';
      set({ error: message, isLoading: false });
    }
  },
  
  deleteProject: async (id) => {
    try {
      set({ isLoading: true, error: null });
      await projectApi.delete(id);
      
      const { projects, currentProject } = get();
      const updatedProjects = projects.filter((p) => p.id !== id);
      set({ 
        projects: updatedProjects,
        currentProject: currentProject?.id === id ? null : currentProject,
        isLoading: false 
      });
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Failed to delete project';
      set({ error: message, isLoading: false });
    }
  },

  generateSceneImage: async (sceneId) => {
    const { currentProject } = get();
    if (!currentProject) return;

    try {
      set({ error: null });
      
      // Find the scene
      const scene = currentProject.scenes.find(s => s.id === sceneId);
      if (!scene) {
        throw new Error('Scene not found');
      }
      
      // Validate that scene has either a sketch or a valid imageDescription for image generation
      const hasSketch = scene.sketch || scene.sketchS3Url;
      const hasValidImageDescription = scene.imageDescription && scene.imageDescription.trim() !== '' && scene.imageDescription !== 'New Scene';
      
      if (!hasSketch && !hasValidImageDescription) {
        throw new Error('Scene must have either a sketch/image or a valid image description to generate an image');
      }
      
      // Register this task so WebhookListener knows to check for updates
      if (typeof window !== 'undefined' && (window as any).__registerWebhookTask) {
        (window as any).__registerWebhookTask(`scene_image_${sceneId}`);
      }
      
      // Save scene data first (description, imageDescription, duration, sketch) before generating
      // This ensures the backend has the latest scene data
      await sceneApi.update(
        currentProject.id,
        sceneId,
        scene.description,
        scene.duration,
        scene.sketch || undefined,
        scene.imageDescription  // Save imageDescription separately
      );
      
      // Trigger image generation (scene images don't use global character/setting)
      await generationApi.generateSceneImage(
        currentProject.id,
        sceneId
      );
      // Webhook will trigger refresh when complete
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Failed to generate image';
      set({ error: message });
      // Unregister task on error
      if (typeof window !== 'undefined' && (window as any).__unregisterWebhookTask) {
        (window as any).__unregisterWebhookTask(`scene_image_${sceneId}`);
      }
      throw error; // Re-throw so component can handle it
    }
  },

  generateSceneVideo: async (sceneId, aspectRatio, voiceoverText) => {
    const { currentProject } = get();
    if (!currentProject) return;

    try {
      set({ error: null });
      
      // Register this task so WebhookListener knows to check for updates
      if (typeof window !== 'undefined' && (window as any).__registerWebhookTask) {
        (window as any).__registerWebhookTask(`scene_video_${sceneId}`);
      }
      
      // Toggles are read from scene data in backend, not passed here
      await generationApi.generateSceneVideo(
        currentProject.id,
        sceneId,
        aspectRatio || currentProject.aspectRatio,
        voiceoverText
      );
      // Webhook will trigger refresh when complete
    } catch (error) {
      // Unregister task on error
      if (typeof window !== 'undefined' && (window as any).__unregisterWebhookTask) {
        (window as any).__unregisterWebhookTask(`scene_video_${sceneId}`);
      }
      const message = error instanceof ApiError ? error.message : 'Failed to generate video';
      set({ error: message });
      throw error; // Re-throw so component can handle it
    }
  },

  generateFullVideo: async () => {
    const { currentProject } = get();
    if (!currentProject) return null;

    try {
      set({ isLoading: true, error: null });
      const response = await generationApi.generateFullVideo(
        currentProject.id,
        currentProject.aspectRatio
      );
      // Webhook will trigger refresh when complete
      set({ isLoading: false });
      return response.final_video_s3_url || null;
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Failed to generate video';
      set({ error: message, isLoading: false });
      return null;
    }
  },

  generateGlobalCharacterImage: async () => {
    const { currentProject } = get();
    if (!currentProject) return;

    try {
      set({ error: null });
      
      // Register this task so WebhookListener knows to check for updates
      if (typeof window !== 'undefined' && (window as any).__registerWebhookTask) {
        (window as any).__registerWebhookTask('global_character');
      }
      
      // Save character data and trigger generation
      // Only send character update, NOT setting update, to keep them independent
      const character = currentProject.globalSettings.character;
      await globalSettingsApi.update(
        currentProject.id,
        {
          name: character.name || '',
          description: character.description || '',
        },
        undefined, // Explicitly don't send setting update
        character.sketch || undefined,
        undefined // Explicitly don't send setting sketch
      );
      // Webhook will trigger refresh when complete
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Failed to generate character image';
      set({ error: message });
      // Unregister task on error
      if (typeof window !== 'undefined' && (window as any).__unregisterWebhookTask) {
        (window as any).__unregisterWebhookTask('global_character');
      }
      throw error; // Re-throw so component can handle it
    }
  },
  
  generateGlobalSettingImage: async () => {
    const { currentProject } = get();
    if (!currentProject) return;

    try {
      set({ error: null });
      
      // Register this task so WebhookListener knows to check for updates
      if (typeof window !== 'undefined' && (window as any).__registerWebhookTask) {
        (window as any).__registerWebhookTask('global_setting');
      }
      
      // Save setting data and trigger generation
      // Only send setting update, NOT character update, to keep them independent
      const setting = currentProject.globalSettings.setting;
      await globalSettingsApi.update(
        currentProject.id,
        undefined, // Explicitly don't send character update
        {
          name: setting.name || '',
          description: setting.description || '',
        },
        undefined, // Explicitly don't send character sketch
        setting.sketch || undefined
      );
      // Webhook will trigger refresh when complete
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Failed to generate setting image';
      set({ error: message });
      // Unregister task on error
      if (typeof window !== 'undefined' && (window as any).__unregisterWebhookTask) {
        (window as any).__unregisterWebhookTask('global_setting');
      }
      throw error; // Re-throw so component can handle it
    }
  },

  refreshProject: async () => {
    const { currentProject } = get();
    if (!currentProject) return;

    try {
      const backendProject = await projectApi.get(currentProject.id);
      const project = backendToFrontendProject(backendProject);
      // Preserve local name if it's different (user might be editing)
      // Only update if the backend name is actually different and we're not in the middle of an edit
      const currentState = get();
      if (currentState.currentProject && currentState.currentProject.name !== project.name) {
        // If local name differs, keep the local one (might be unsaved edit)
        // But if backend name is newer (updated_at is later), use backend
        // For now, prefer backend name to ensure consistency
      }
      set({ currentProject: project });
    } catch (error) {
      console.error('Failed to refresh project:', error);
    }
  },

  refreshGlobalCharacter: async () => {
    const { currentProject } = get();
    if (!currentProject) {
      console.log('[refreshGlobalCharacter] No current project');
      return;
    }

    try {
      console.log('[refreshGlobalCharacter] Fetching project from API...');
      const backendProject = await projectApi.get(currentProject.id);
      console.log('[refreshGlobalCharacter] Backend project received:', {
        character_image: backendProject.global_character?.generated_image_s3_url,
        character_description: backendProject.global_character?.description,
      });
      
      const project = backendToFrontendProject(backendProject);
      console.log('[refreshGlobalCharacter] Converted project character:', {
        name: project.globalSettings.character.name,
        image: project.globalSettings.character.image,
      });
      
      // Only update the global character part
      set({
        currentProject: {
          ...currentProject,
      globalSettings: {
            ...currentProject.globalSettings,
            character: project.globalSettings.character,
          },
        },
      });
      console.log('[refreshGlobalCharacter] State updated successfully');
    } catch (error) {
      console.error('[refreshGlobalCharacter] Failed to refresh global character:', error);
    }
  },

  refreshGlobalSetting: async () => {
    const { currentProject } = get();
    if (!currentProject) {
      console.log('[refreshGlobalSetting] No current project');
      return;
    }

    try {
      console.log('[refreshGlobalSetting] Fetching project from API...');
      const backendProject = await projectApi.get(currentProject.id);
      console.log('[refreshGlobalSetting] Backend project received:', {
        setting_image: backendProject.global_setting?.generated_image_s3_url,
        setting_description: backendProject.global_setting?.description,
      });
      
      const project = backendToFrontendProject(backendProject);
      console.log('[refreshGlobalSetting] Converted project setting:', {
        name: project.globalSettings.setting.name,
        image: project.globalSettings.setting.image,
      });

      // Only update the global setting part
      set({
        currentProject: {
          ...currentProject,
          globalSettings: {
            ...currentProject.globalSettings,
            setting: project.globalSettings.setting,
          },
        },
      });
      console.log('[refreshGlobalSetting] State updated successfully');
    } catch (error) {
      console.error('[refreshGlobalSetting] Failed to refresh global setting:', error);
    }
  },

  refreshScene: async (sceneId: string, presignedUrl?: string) => {
    const { currentProject } = get();
    if (!currentProject) {
      console.log('[refreshScene] No current project');
      return;
    }

    try {
      console.log(`[refreshScene] Fetching project from API for scene ${sceneId}...`);
      const backendProject = await projectApi.get(currentProject.id);
      const project = backendToFrontendProject(backendProject);
      
      // Find the updated scene
      const updatedScene = project.scenes.find(s => s.id === sceneId);
      if (!updatedScene) {
        console.log(`[refreshScene] Scene ${sceneId} not found in updated project`);
        return;
      }
      
      console.log(`[refreshScene] Updated scene data:`, {
        id: updatedScene.id,
        generatedImage: updatedScene.generatedImage,
        generatedVideo: updatedScene.generatedVideo,
        status: updatedScene.status,
      });
      
      // Only update the specific scene
      // If presigned URL is provided, use it directly for the video
      const updatedScenes = currentProject.scenes.map((scene) => {
        if (scene.id === sceneId) {
          const sceneUpdate = { ...updatedScene };
          // If presigned URL is provided, use it for the generated video
          // This takes priority over the S3 URL from the API
          if (presignedUrl) {
            sceneUpdate.generatedVideo = presignedUrl;
            console.log(`[refreshScene] Using presigned URL for video: ${presignedUrl.substring(0, 50)}...`);
          } else {
            console.log(`[refreshScene] No presigned URL provided, using S3 URL from API: ${sceneUpdate.generatedVideo || 'none'}`);
          }
          return sceneUpdate;
        }
        return scene;
      });
      
      set({
        currentProject: {
          ...currentProject,
          scenes: updatedScenes,
        },
      });
      console.log(`[refreshScene] State updated successfully for scene ${sceneId}`);
    } catch (error) {
      console.error(`[refreshScene] Failed to refresh scene ${sceneId}:`, error);
    }
  },
}));
