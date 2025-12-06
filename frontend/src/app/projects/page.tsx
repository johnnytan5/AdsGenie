'use client';

import { useRouter } from 'next/navigation';
import { useProjectStore } from '@/store/projectStore';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ArrowLeft, Plus, Trash2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import LiquidEther from '@/components/LiquidEther';
import CursorGenie from '@/components/CursorGenie';

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
    <div className="min-h-screen relative p-8">
      {/* Cursor Following Genie */}
      <CursorGenie />
      
      {/* LiquidEther Backdrop */}
      <div style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0, zIndex: 0 }}>
        <LiquidEther
          colors={['#5227FF', '#FF9FFC', '#B19EEF']}
          mouseForce={20}
          cursorSize={100}
          isViscous={false}
          viscous={30}
          iterationsViscous={32}
          iterationsPoisson={32}
          resolution={0.5}
          isBounce={false}
          autoDemo={true}
          autoSpeed={0.5}
          autoIntensity={2.2}
          takeoverDuration={0.25}
          autoResumeDelay={3000}
          autoRampDuration={0.6}
        />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 mb-2">My Projects</h1>
            <p className="text-slate-600">
              How about unlimited video magic?
            </p>
          </div>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => router.push('/')}
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
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <Button
              onClick={() => router.push('/aspect-ratio')}
              style={{
                backgroundColor: '#5227FF',
                color: 'white',
                border: 'none',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#4218E6';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#5227FF';
              }}
            >
              <Plus className="w-4 h-4 mr-2" />
              New Project
            </Button>
          </div>
        </div>

        {/* Projects Grid */}
        {!isLoading && projects.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-slate-400 text-lg mb-4">No projects yet</p>
            <Button 
              onClick={() => router.push('/aspect-ratio')}
              style={{
                backgroundColor: '#5227FF',
                color: 'white',
                border: 'none',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#4218E6';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#5227FF';
              }}
            >
              Create Your First Project
            </Button>
          </div>
        ) : !isLoading && projects.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project, index) => (
              <Card
                key={project.id}
                onClick={() => handleOpenProject(project.id)}
                className="p-6 hover:shadow-md transition-all duration-500 bg-white/90 backdrop-blur-sm animate-fade-in-up"
                style={{
                  animationDelay: `${index * 100}ms`,
                  animationFillMode: 'both',
                }}
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
                          style={{
                            backgroundColor: '#5227FF',
                            color: 'white',
                            border: 'none',
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.backgroundColor = '#4218E6';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.backgroundColor = '#5227FF';
                          }}
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
        ) : null}
      </div>
    </div>
  );
}

