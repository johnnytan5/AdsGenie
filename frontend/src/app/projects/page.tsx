'use client';

import { useRouter } from 'next/navigation';
import { useProjectStore } from '@/store/projectStore';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ArrowLeft, Plus, Trash2 } from 'lucide-react';
import { useState, useEffect } from 'react';

export default function ProjectsPage() {
  const router = useRouter();
  const { projects, loadProject, deleteProject, loadProjects, isLoading } = useProjectStore();
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const handleOpenProject = async (id: string) => {
    try {
      await loadProject(id);
      router.push(`/editor/${id}`);
    } catch (error) {
      console.error('Failed to load project:', error);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this project?')) {
      setDeletingId(id);
      deleteProject(id);
      setDeletingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 mb-2">My Projects</h1>
            <p className="text-slate-600">
              Manage and continue working on your video ad projects
            </p>
          </div>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => router.push('/')}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <Button
              onClick={() => router.push('/aspect-ratio')}
            >
              <Plus className="w-4 h-4 mr-2" />
              New Project
            </Button>
          </div>
        </div>

        {/* Projects Grid */}
        {isLoading ? (
          <div className="text-center py-16">
            <p className="text-slate-400 text-lg">Loading projects...</p>
          </div>
        ) : projects.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-slate-400 text-lg mb-4">No projects yet</p>
            <Button onClick={() => router.push('/aspect-ratio')}>
              Create Your First Project
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <Card
                key={project.id}
                onClick={() => handleOpenProject(project.id)}
                className="p-6 hover:shadow-md transition-shadow"
              >
                <div className="space-y-4">
                  {/* Thumbnail */}
                  <div className="aspect-video bg-slate-100 rounded-lg border border-slate-200 overflow-hidden">
                    {project.thumbnail ? (
                      <img
                        src={project.thumbnail}
                        alt={project.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <span className="text-slate-400 text-sm">No thumbnail</span>
                      </div>
                    )}
                  </div>

                  {/* Project Info */}
                  <div>
                    <h3 className="font-semibold text-slate-900 mb-1">
                      {project.name}
                    </h3>
                    <div className="flex items-center justify-between text-sm text-slate-500">
                      <span>{project.aspectRatio}</span>
                      <span>
                        {new Date(project.updatedAt).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">
                      {project.scenes.length} scenes
                    </p>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 pt-2 border-t border-slate-200">
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenProject(project.id);
                      }}
                      className="flex-1"
                    >
                      Open Project
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => handleDelete(project.id, e)}
                      disabled={deletingId === project.id}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

