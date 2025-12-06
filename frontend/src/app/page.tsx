'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/Button';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full text-center space-y-8">
        <div className="space-y-4">
          <h1 className="text-5xl font-bold text-slate-900">Ads Genie</h1>
          <p className="text-xl text-slate-600">
            Create stunning video ads with AI-powered generation
          </p>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Link href="/aspect-ratio">
            <Button size="lg" className="w-full sm:w-auto min-w-[200px]">
              Create New Project
            </Button>
          </Link>
          <Link href="/projects">
            <Button variant="outline" size="lg" className="w-full sm:w-auto min-w-[200px]">
              My Projects
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
