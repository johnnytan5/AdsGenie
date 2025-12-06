'use client';

import { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useProjectStore } from '@/store/projectStore';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ArrowLeft, Music, Mic, Download } from 'lucide-react';
import { WebhookListener } from '@/components/WebhookListener';

type MusicType = 'happy' | 'sad' | 'energetic' | 'calm' | 'dramatic' | 'romantic' | 'party' | 'mysterious' | 'inspiring' | 'upbeat' | 'ambient';
type Mood = 'uplifting' | 'melancholic' | 'intense' | 'peaceful' | 'playful' | 'serious';
type Tempo = 'slow' | 'medium' | 'fast';

export default function AudioPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const projectId = searchParams.get('projectId');
  
  const { currentProject, loadProject } = useProjectStore();
  const [isLoading, setIsLoading] = useState(true);
  
  // BGM State
  const [bgmEnabled, setBgmEnabled] = useState(false);
  const [bgmMusicType, setBgmMusicType] = useState<MusicType>('upbeat');
  const [bgmMood, setBgmMood] = useState<Mood | ''>('');
  const [bgmTempo, setBgmTempo] = useState<Tempo>('medium');
  const [isGeneratingBGM, setIsGeneratingBGM] = useState(false);
  const [bgmStatus, setBgmStatus] = useState<'idle' | 'processing' | 'done' | 'failed'>('idle');
  
  // TTS State
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const [ttsText, setTtsText] = useState('');
  const [ttsVoiceId, setTtsVoiceId] = useState('');
  const [isGeneratingTTS, setIsGeneratingTTS] = useState(false);
  const [ttsStatus, setTtsStatus] = useState<'idle' | 'processing' | 'done' | 'failed'>('idle');
  
  // Video with audio preview
  const [videoWithAudioUrl, setVideoWithAudioUrl] = useState<string | null>(null);
  
  // Video duration state
  const [actualVideoDuration, setActualVideoDuration] = useState<number | null>(null);

  useEffect(() => {
    if (projectId) {
      loadProject(projectId)
        .then(() => {
          setIsLoading(false);
          // Fallback to calculated duration initially
          const totalDuration = currentProject?.scenes.reduce((sum, scene) => sum + (scene.duration || 6), 0) || 0;
          setActualVideoDuration(totalDuration);
        })
        .catch((error) => {
          console.error('Failed to load project:', error);
          setIsLoading(false);
        });
    } else {
      setIsLoading(false);
    }
  }, [projectId, loadProject]);

  // Get video duration from the video element when it loads
  useEffect(() => {
    if (!currentProject?.finalVideoS3Url) return;

    const videoElement = document.querySelector('video[src*="final_video"]') as HTMLVideoElement;
    if (!videoElement) return;

    const handleLoadedMetadata = () => {
      if (videoElement.duration && !isNaN(videoElement.duration)) {
        setActualVideoDuration(Math.round(videoElement.duration));
      }
    };

    videoElement.addEventListener('loadedmetadata', handleLoadedMetadata);
    
    // If metadata is already loaded
    if (videoElement.readyState >= 1) {
      handleLoadedMetadata();
    }

    return () => {
      videoElement.removeEventListener('loadedmetadata', handleLoadedMetadata);
    };
  }, [currentProject?.finalVideoS3Url]);

  // Use actual video duration if available, otherwise fallback to calculated
  const totalDuration = actualVideoDuration !== null 
    ? actualVideoDuration 
    : (currentProject
        ? currentProject.scenes.reduce((sum, scene) => sum + (scene.duration || 6), 0)
        : 0);

  // Get video description (could be from project or scenes)
  const videoDescription = currentProject
    ? currentProject.scenes.map(s => s.description).filter(Boolean).join('. ') || currentProject.name
    : '';

  const handleGenerateBGM = async () => {
    if (!projectId || !currentProject?.finalVideoS3Url || !bgmEnabled) return;

    setIsGeneratingBGM(true);
    setBgmStatus('processing');

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/projects/${projectId}/add-audio-to-video`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            audio_type: 'background_music',
            video_description: videoDescription,
            duration: totalDuration, // Use actual video duration
            tts_text: null,
            voice_id: null,
            music_type: bgmMusicType,
            mood: bgmMood || null,
            tempo: bgmTempo,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to generate BGM');
      }

      // Webhook will update status
      // Register webhook task
      if ((window as any).__registerWebhookTask) {
        (window as any).__registerWebhookTask(`video_audio_full_bgm`);
      }
      
      // Note: Status will be updated via webhook
    } catch (error) {
      console.error('Error generating BGM:', error);
      setBgmStatus('failed');
      setIsGeneratingBGM(false);
    }
  };

  const handleGenerateTTS = async () => {
    if (!projectId || !currentProject?.finalVideoS3Url || !ttsEnabled || !ttsText.trim()) return;

    setIsGeneratingTTS(true);
    setTtsStatus('processing');

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/projects/${projectId}/add-audio-to-video`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            audio_type: 'text_to_speech',
            video_description: videoDescription,
            duration: totalDuration, // Use actual video duration
            tts_text: ttsText,
            voice_id: ttsVoiceId || undefined,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to generate TTS');
      }

      // Webhook will update status
      if ((window as any).__registerWebhookTask) {
        (window as any).__registerWebhookTask(`video_audio_full_tts`);
      }
      
      // Note: Status will be updated via webhook
    } catch (error) {
      console.error('Error generating TTS:', error);
      setTtsStatus('failed');
      setIsGeneratingTTS(false);
    }
  };

  // Listen for webhook updates
  useEffect(() => {
    const handleWebhook = (event: CustomEvent) => {
      const { taskType, status, presignedUrl } = event.detail;
      
      if (taskType === 'video_audio_full_bgm') {
        if (status === 'done') {
          setBgmStatus('done');
          setIsGeneratingBGM(false);
          if (presignedUrl) {
            setVideoWithAudioUrl(presignedUrl);
          }
        } else if (status === 'failed') {
          setBgmStatus('failed');
          setIsGeneratingBGM(false);
        }
      } else if (taskType === 'video_audio_full_tts') {
        if (status === 'done') {
          setTtsStatus('done');
          setIsGeneratingTTS(false);
          if (presignedUrl) {
            setVideoWithAudioUrl(presignedUrl);
          }
        } else if (status === 'failed') {
          setTtsStatus('failed');
          setIsGeneratingTTS(false);
        }
      }
    };

    window.addEventListener('webhook-update', handleWebhook as EventListener);
    return () => {
      window.removeEventListener('webhook-update', handleWebhook as EventListener);
    };
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-slate-400">Loading project...</p>
      </div>
    );
  }

  if (!projectId || !currentProject) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-400 mb-4">Project not found</p>
          <Button variant="outline" onClick={() => router.push('/projects')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Projects
          </Button>
        </div>
      </div>
    );
  }

  if (!currentProject.finalVideoS3Url) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-400 mb-4">Please generate a full video first</p>
          <Button variant="outline" onClick={() => router.push(`/editor/${projectId}`)}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Editor
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <WebhookListener />
      
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push(`/editor/${projectId}`)}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Editor
            </Button>
            <div>
              <h1 className="text-xl font-semibold text-slate-900">Audio Enhancement</h1>
              <p className="text-sm text-slate-500">{currentProject.name}</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Video Preview Section */}
        {(videoWithAudioUrl || currentProject.finalVideoS3Url) && (
          <div className="bg-white rounded-lg border border-slate-200 p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-slate-900">
                {videoWithAudioUrl ? 'Enhanced Video with Audio' : 'Original Video'}
              </h2>
              {videoWithAudioUrl && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const link = document.createElement('a');
                    link.href = videoWithAudioUrl;
                    link.download = 'enhanced-video.mp4';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                  }}
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download
                </Button>
              )}
            </div>
            <div className="bg-slate-900 rounded-lg overflow-hidden">
              <video
                src={videoWithAudioUrl || currentProject.finalVideoS3Url || undefined}
                controls
                className="w-full h-auto"
                onLoadedMetadata={(e) => {
                  const video = e.currentTarget;
                  if (video.duration && !isNaN(video.duration)) {
                    setActualVideoDuration(Math.round(video.duration));
                  }
                }}
              >
                Your browser does not support the video tag.
              </video>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* BGM Section */}
          <div className="bg-white rounded-lg border border-slate-200 p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                <Music className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Background Music</h2>
                <p className="text-sm text-slate-500">Generate BGM for your video</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="bgm-enabled"
                  checked={bgmEnabled}
                  onChange={(e) => setBgmEnabled(e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="bgm-enabled" className="text-sm font-medium text-slate-700">
                  Enable Background Music
                </label>
              </div>

              {bgmEnabled && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Music Type
                    </label>
                <select
                  value={bgmMusicType}
                  onChange={(e) => setBgmMusicType(e.target.value as MusicType)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="happy">Happy</option>
                  <option value="sad">Sad</option>
                  <option value="energetic">Energetic</option>
                  <option value="calm">Calm</option>
                  <option value="dramatic">Dramatic</option>
                  <option value="romantic">Romantic</option>
                  <option value="party">Party</option>
                  <option value="mysterious">Mysterious</option>
                  <option value="inspiring">Inspiring</option>
                  <option value="upbeat">Upbeat</option>
                  <option value="ambient">Ambient</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Mood (Optional)
                </label>
                <select
                  value={bgmMood}
                  onChange={(e) => setBgmMood(e.target.value as Mood | '')}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Default</option>
                  <option value="uplifting">Uplifting</option>
                  <option value="melancholic">Melancholic</option>
                  <option value="intense">Intense</option>
                  <option value="peaceful">Peaceful</option>
                  <option value="playful">Playful</option>
                  <option value="serious">Serious</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Tempo
                </label>
                <select
                  value={bgmTempo}
                  onChange={(e) => setBgmTempo(e.target.value as Tempo)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="slow">Slow</option>
                  <option value="medium">Medium</option>
                  <option value="fast">Fast</option>
                </select>
              </div>

                  <div className="pt-4">
                    <Button
                      variant="primary"
                      onClick={handleGenerateBGM}
                      disabled={isGeneratingBGM || !currentProject.finalVideoS3Url || !bgmEnabled}
                      loading={isGeneratingBGM}
                      className="w-full"
                    >
                      <Music className="w-4 h-4 mr-2" />
                      {isGeneratingBGM ? 'Generating BGM...' : 'Generate BGM'}
                    </Button>
                    {bgmStatus === 'done' && (
                      <p className="mt-2 text-sm text-green-600">BGM generated successfully!</p>
                    )}
                    {bgmStatus === 'failed' && (
                      <p className="mt-2 text-sm text-red-600">BGM generation failed. Please try again.</p>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>

          {/* TTS Section */}
          <div className="bg-white rounded-lg border border-slate-200 p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center">
                <Mic className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Text-to-Speech</h2>
                <p className="text-sm text-slate-500">Add narration to your video</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="tts-enabled"
                  checked={ttsEnabled}
                  onChange={(e) => setTtsEnabled(e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="tts-enabled" className="text-sm font-medium text-slate-700">
                  Enable TTS
                </label>
              </div>

              {ttsEnabled && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Narration Text
                    </label>
                    <textarea
                      value={ttsText}
                      onChange={(e) => setTtsText(e.target.value)}
                      placeholder="Enter the narration text for your video..."
                      rows={6}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Voice ID (Optional)
                    </label>
                    <Input
                      type="text"
                      value={ttsVoiceId}
                      onChange={(e) => setTtsVoiceId(e.target.value)}
                      placeholder="Leave empty for default voice"
                    />
                  </div>

                  <div className="pt-4">
                    <Button
                      variant="primary"
                      onClick={handleGenerateTTS}
                      disabled={isGeneratingTTS || !ttsText.trim() || !currentProject.finalVideoS3Url}
                      loading={isGeneratingTTS}
                      className="w-full"
                    >
                      <Mic className="w-4 h-4 mr-2" />
                      {isGeneratingTTS ? 'Generating TTS...' : 'Generate TTS'}
                    </Button>
                    {ttsStatus === 'done' && (
                      <p className="mt-2 text-sm text-green-600">TTS generated successfully!</p>
                    )}
                    {ttsStatus === 'failed' && (
                      <p className="mt-2 text-sm text-red-600">TTS generation failed. Please try again.</p>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Video Info */}
        <div className="mt-6 bg-white rounded-lg border border-slate-200 p-6">
          <h3 className="text-sm font-semibold text-slate-900 mb-2">Video Information</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-slate-500">Video Duration:</span>
              <span className="ml-2 font-medium text-slate-900">
                {actualVideoDuration !== null ? `${actualVideoDuration}s` : 'Loading...'}
              </span>
              {actualVideoDuration !== null && (
                <span className="ml-2 text-xs text-slate-400">
                  ({Math.floor(actualVideoDuration / 60)}m {actualVideoDuration % 60}s)
                </span>
              )}
            </div>
            <div>
              <span className="text-slate-500">Scenes:</span>
              <span className="ml-2 font-medium text-slate-900">{currentProject.scenes.length}</span>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
