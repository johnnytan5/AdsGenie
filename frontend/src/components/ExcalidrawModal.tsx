'use client';

import { useState, useCallback, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { Button } from './ui/Button';
import { X } from 'lucide-react';
import '@excalidraw/excalidraw/index.css';

// Dynamically import Excalidraw to avoid SSR issues
const Excalidraw = dynamic(
  async () => (await import('@excalidraw/excalidraw')).Excalidraw,
  {
    ssr: false,
  }
);

interface ExcalidrawModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (file: File) => void;
}

export const ExcalidrawModal: React.FC<ExcalidrawModalProps> = ({
  isOpen,
  onClose,
  onSave,
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const [excalidrawAPI, setExcalidrawAPI] = useState<any>(null);

  // Reset API when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setExcalidrawAPI(null);
    }
  }, [isOpen]);

  const handleFinishSketch = useCallback(async () => {
    if (!excalidrawAPI) {
      console.error('Excalidraw API not available');
      alert('Excalidraw is not ready. Please wait a moment and try again.');
      return;
    }

    // Verify API methods exist
    if (typeof excalidrawAPI.getSceneElements !== 'function') {
      console.error('getSceneElements is not a function');
      alert('Excalidraw API is not properly initialized.');
      return;
    }

    setIsExporting(true);
    try {
      const { exportToCanvas } = await import('@excalidraw/excalidraw');
      
      // Get current scene data
      const elements = excalidrawAPI.getSceneElements();
      const appState = excalidrawAPI.getAppState();
      const files = excalidrawAPI.getFiles();

      console.log('Exporting sketch with elements:', elements?.length || 0);
      console.log('App state:', appState);
      console.log('Files:', files);

      // Check if there are any elements to export
      if (!elements || elements.length === 0) {
        alert('Please draw something before finishing the sketch.');
        setIsExporting(false);
        return;
      }

      // Export to canvas
      const canvas = await exportToCanvas({
        elements,
        appState,
        files,
        getDimensions: (width: number, height: number) => {
          // Export at a good resolution for image generation
          return { width: 1024, height: 1024 };
        },
      });

      console.log('Canvas created, size:', canvas.width, 'x', canvas.height);

      // Convert canvas to blob, then to File
      canvas.toBlob((blob: Blob | null) => {
        if (blob) {
          console.log('Blob created, size:', blob.size, 'bytes');
          const file = new File([blob], 'sketch.png', { type: 'image/png' });
          console.log('File created:', file.name, file.size, 'bytes');
          onSave(file);
          onClose();
        } else {
          console.error('Failed to create blob from canvas');
          alert('Failed to export sketch. Please try again.');
        }
        setIsExporting(false);
      }, 'image/png');
    } catch (error) {
      console.error('Error exporting sketch:', error);
      alert(`Error exporting sketch: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setIsExporting(false);
    }
  }, [excalidrawAPI, onSave, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-white rounded-lg shadow-xl w-full h-full max-w-6xl max-h-[90vh] mx-4 my-4 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-900">Draw Sketch</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-slate-600" />
          </button>
        </div>

        {/* Excalidraw Editor */}
        <div className="flex-1 overflow-hidden">
          <Excalidraw
            excalidrawAPI={(api: any) => {
              console.log('Excalidraw API callback called with:', api);
              if (api) {
                setExcalidrawAPI(api);
                console.log('Excalidraw API methods:', Object.keys(api));
              }
            }}
          />
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-3 p-4 border-t border-slate-200 bg-slate-50">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isExporting}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleFinishSketch}
            disabled={isExporting}
            loading={isExporting}
          >
            Finish Sketch
          </Button>
        </div>
      </div>
    </div>
  );
};

