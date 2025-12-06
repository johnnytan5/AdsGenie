'use client';

import { useRouter } from 'next/navigation';
import { Button } from './ui/Button';
import { X, Download, ArrowLeft, Music } from 'lucide-react';

interface VideoPreviewModalProps {
  videoUrl: string | null;
  isOpen: boolean;
  onClose: () => void;
  onExport: () => void;
  onBackToEditing: () => void;
  projectId?: string;
}

export const VideoPreviewModal: React.FC<VideoPreviewModalProps> = ({
  videoUrl,
  isOpen,
  onClose,
  onExport,
  onBackToEditing,
  projectId,
}) => {
  const router = useRouter();
  
  if (!isOpen || !videoUrl) return null;

  const handleExport = () => {
    // Create a temporary link to download the video
    const link = document.createElement('a');
    link.href = videoUrl;
    link.download = 'generated-video.mp4';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    onExport();
  };

  const handleAudioEnhancement = () => {
    if (projectId) {
      router.push(`/audio?projectId=${projectId}`);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200">
          <h2 className="text-xl font-semibold text-slate-900">Generated Video Preview</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-slate-600" />
          </button>
        </div>

        {/* Video Player */}
        <div className="flex-1 p-6 overflow-auto">
          <div className="bg-slate-900 rounded-lg overflow-hidden">
            <video
              src={videoUrl}
              controls
              autoPlay
              className="w-full h-full"
            >
              Your browser does not support the video tag.
            </video>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between p-6 border-t border-slate-200 bg-slate-50">
          <Button
            variant="outline"
            onClick={onBackToEditing}
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
            Back to Editing
          </Button>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={handleAudioEnhancement}
              disabled={!projectId}
              style={{
                borderColor: '#5227FF',
                color: '#5227FF',
              }}
              onMouseEnter={(e) => {
                if (!e.currentTarget.disabled) {
                  e.currentTarget.style.backgroundColor = '#5227FF';
                  e.currentTarget.style.color = 'white';
                }
              }}
              onMouseLeave={(e) => {
                if (!e.currentTarget.disabled) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = '#5227FF';
                }
              }}
            >
              <Music className="w-4 h-4 mr-2" />
              Audio Enhancement
            </Button>
            <Button
              variant="primary"
              onClick={handleExport}
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
              <Download className="w-4 h-4 mr-2" />
              Export Video
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

