'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { useProjectStore } from '@/store/projectStore';

/**
 * WebhookListener component that checks for webhooks only when generation tasks are active.
 * 
 * No constant polling - only checks when we know a task is running.
 * Uses a lightweight check mechanism that doesn't interfere with typing.
 */
export function WebhookListener() {
  const { refreshProject, currentProject, refreshGlobalCharacter, refreshGlobalSetting, refreshScene } = useProjectStore();
  const activeTasksRef = useRef<Set<string>>(new Set());
  const checkIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const [activeTasksCount, setActiveTasksCount] = useState(0);

  // Function to start/stop checking based on active tasks
  const updateCheckInterval = useCallback(() => {
    if (!currentProject) {
      // Clear interval if no project
      if (checkIntervalRef.current) {
        clearInterval(checkIntervalRef.current);
        checkIntervalRef.current = null;
      }
      return;
    }

    // Only check for webhooks if there are active tasks
    if (activeTasksRef.current.size === 0) {
      if (checkIntervalRef.current) {
        clearInterval(checkIntervalRef.current);
        checkIntervalRef.current = null;
      }
      return;
    }

    // Set up interval to check for webhooks (only when tasks are active)
    if (!checkIntervalRef.current) {
      console.log(`[WebhookListener] Starting webhook checks for ${activeTasksRef.current.size} active tasks`);
      checkIntervalRef.current = setInterval(async () => {
        try {
          const response = await fetch(
            `/api/webhooks/project-update?project_id=${currentProject.id}`
          );
          if (!response.ok) {
            console.error(`[WebhookListener] Failed to fetch webhooks: ${response.status}`);
            return;
          }
          
          const data = await response.json();
          const webhooks = data.webhooks || [];

          if (webhooks.length > 0) {
            console.log(`[WebhookListener] Received ${webhooks.length} webhook(s)`, webhooks);
          }

          for (const webhook of webhooks) {
            const { task_type, status, presigned_url } = webhook;
            
            console.log(`[WebhookListener] Processing webhook: ${task_type} for project ${currentProject.id} with status ${status || 'done'}${presigned_url ? ' (with presigned URL)' : ''}`);

            // Remove from active tasks
            activeTasksRef.current.delete(task_type);
            setActiveTasksCount(activeTasksRef.current.size);

            // Refresh only the specific part that changed
            if (task_type === 'global_character') {
              console.log(`[WebhookListener] Refreshing global character`);
              await refreshGlobalCharacter();
            } else if (task_type === 'global_setting') {
              console.log(`[WebhookListener] Refreshing global setting`);
              await refreshGlobalSetting();
            } else if (task_type.startsWith('scene_image_')) {
              // Refresh only the specific scene
              const sceneId = task_type.replace('scene_image_', '');
              console.log(`[WebhookListener] Refreshing scene ${sceneId} for image update`);
              await refreshScene(sceneId);
            } else if (task_type.startsWith('scene_video_')) {
              // Refresh only the specific scene, use presigned URL if available
              const sceneId = task_type.replace('scene_video_', '');
              console.log(`[WebhookListener] Refreshing scene ${sceneId} for video update${presigned_url ? ' with presigned URL' : ''}`);
              await refreshScene(sceneId, presigned_url);
            } else if (task_type === 'final_video') {
              console.log(`[WebhookListener] Refreshing project for final video`);
              await refreshProject();
            } else {
              // Unknown task type, refresh whole project as fallback
              console.log(`[WebhookListener] Refreshing project for unknown task type: ${task_type}`);
              await refreshProject();
            }
          }

          // Stop checking if no more active tasks
          if (activeTasksRef.current.size === 0 && checkIntervalRef.current) {
            console.log(`[WebhookListener] No more active tasks, stopping webhook checks`);
            clearInterval(checkIntervalRef.current);
            checkIntervalRef.current = null;
          }
        } catch (error) {
          console.error('[WebhookListener] Error checking for webhooks:', error);
        }
      }, 2000); // Check every 2 seconds when tasks are active
    }
  }, [currentProject, refreshProject, refreshGlobalCharacter, refreshGlobalSetting, refreshScene]);

  // Update interval when active tasks count changes or project changes
  useEffect(() => {
    updateCheckInterval();

    return () => {
      if (checkIntervalRef.current) {
        clearInterval(checkIntervalRef.current);
        checkIntervalRef.current = null;
      }
    };
  }, [currentProject, activeTasksCount, updateCheckInterval]);

  // Expose method to register active tasks (called by generation functions)
  useEffect(() => {
    // Store reference in window so generation functions can register tasks
    (window as any).__registerWebhookTask = (taskType: string) => {
      console.log(`[WebhookListener] Registering task: ${taskType}`);
      activeTasksRef.current.add(taskType);
      setActiveTasksCount(activeTasksRef.current.size);
      // Trigger interval update
      updateCheckInterval();
    };

    (window as any).__unregisterWebhookTask = (taskType: string) => {
      console.log(`[WebhookListener] Unregistering task: ${taskType}`);
      activeTasksRef.current.delete(taskType);
      setActiveTasksCount(activeTasksRef.current.size);
      // Trigger interval update
      updateCheckInterval();
    };

    return () => {
      delete (window as any).__registerWebhookTask;
      delete (window as any).__unregisterWebhookTask;
    };
  }, [updateCheckInterval]);

  return null; // This component doesn't render anything
}
