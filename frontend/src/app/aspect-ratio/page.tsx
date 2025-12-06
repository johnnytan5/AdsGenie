'use client';

import { useRouter } from 'next/navigation';
import { useProjectStore, AspectRatio } from '@/store/projectStore';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { UserJourney } from '@/components/UserJourney';

export default function AspectRatioPage() {
  const router = useRouter();
  const { aspectRatio, setAspectRatio, createProject } = useProjectStore();

  const handleSelect = (ratio: AspectRatio) => {
    setAspectRatio(ratio);
  };

  const handleContinue = async () => {
    if (aspectRatio) {
      try {
        const project = await createProject('Untitled Project', aspectRatio);
        // Navigate to editor with project ID in URL
        router.push(`/editor/${project.id}`);
      } catch (error) {
        console.error('Failed to create project:', error);
        // If creation fails, still try to navigate (will redirect back if no project)
        router.push('/projects');
      }
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* User Journey Progress */}
      <UserJourney />
      
      <div className="flex-1 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">
            Choose Aspect Ratio
          </h1>
          <p className="text-slate-600">
            Select the format for your video ad
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <Card
            onClick={() => handleSelect('16:9')}
            className={`p-8 ${aspectRatio === '16:9' ? 'ring-2 ring-blue-500 border-blue-500' : ''}`}
          >
            <div className="space-y-4">
              <div className="aspect-video bg-gradient-to-br from-blue-100 to-blue-200 rounded-lg flex items-center justify-center">
                <span className="text-2xl font-semibold text-blue-700">16:9</span>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-slate-900 mb-1">
                  Landscape (16:9)
                </h3>
                <p className="text-slate-600 text-sm">
                  Perfect for YouTube, desktop ads, and widescreen displays
                </p>
              </div>
            </div>
          </Card>

          <Card
            onClick={() => handleSelect('9:16')}
            className={`p-8 ${aspectRatio === '9:16' ? 'ring-2 ring-blue-500 border-blue-500' : ''}`}
          >
            <div className="space-y-4">
              <div className="aspect-[9/16] bg-gradient-to-br from-purple-100 to-purple-200 rounded-lg flex items-center justify-center max-w-[200px] mx-auto">
                <span className="text-xl font-semibold text-purple-700">9:16</span>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-slate-900 mb-1">
                  Portrait (9:16)
                </h3>
                <p className="text-slate-600 text-sm">
                  Ideal for TikTok, Instagram Reels, and mobile-first content
                </p>
              </div>
            </div>
          </Card>
        </div>

        <div className="flex justify-end gap-4">
          <Button
            variant="outline"
            onClick={() => router.push('/')}
          >
            Back
          </Button>
          <Button
            onClick={handleContinue}
            disabled={!aspectRatio}
          >
            Continue
          </Button>
        </div>
        </div>
      </div>
    </div>
  );
}

