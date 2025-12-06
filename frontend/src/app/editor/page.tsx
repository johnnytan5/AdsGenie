'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useProjectStore } from '@/store/projectStore';

/**
 * Legacy editor page - redirects to aspect-ratio if no project,
 * or to /editor/[projectId] if project exists
 */
export default function EditorPage() {
  const router = useRouter();
  const { currentProject, aspectRatio } = useProjectStore();

  useEffect(() => {
    if (currentProject) {
      // If we have a project, redirect to the project-specific editor
      router.replace(`/editor/${currentProject.id}`);
    } else if (aspectRatio) {
      // If we have aspect ratio but no project, redirect to aspect-ratio to create one
      router.replace('/aspect-ratio');
    } else {
      // No project and no aspect ratio, go to aspect-ratio page
      router.replace('/aspect-ratio');
    }
  }, [currentProject, aspectRatio, router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-slate-400">Redirecting...</p>
    </div>
  );
}
