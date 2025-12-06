"""
Video and audio combination utilities using FFmpeg.
"""
import subprocess
import tempfile
import os
from typing import Optional

from app.core.s3 import download_file_from_s3, extract_s3_key_from_url, upload_file_to_s3


async def combine_video_and_audio(
    video_s3_url: str,
    audio_bytes: bytes,
    project_id: str,
    output_key: Optional[str] = None,
) -> Optional[str]:
    """
    Combine video and audio using FFmpeg.

    Args:
        video_s3_url: S3 URL of the video file
        audio_bytes: Audio bytes to combine with video
        project_id: Project ID for generating output S3 key
        output_key: Optional custom S3 key for output (defaults to final_video_with_audio.mp4)

    Returns:
        S3 URL of the combined video with audio, or None if failed
    """
    temp_dir = tempfile.mkdtemp()
    video_file = None
    audio_file = None
    output_file = None

    try:
        # Download video from S3
        video_s3_key = extract_s3_key_from_url(video_s3_url)
        if not video_s3_key:
            print("[VIDEO AUDIO COMBINER] Failed to extract S3 key from video URL")
            return None

        video_bytes = download_file_from_s3(video_s3_key)
        if not video_bytes:
            print("[VIDEO AUDIO COMBINER] Failed to download video from S3")
            return None

        # Save video to temp file
        video_file = os.path.join(temp_dir, "video.mp4")
        with open(video_file, "wb") as f:
            f.write(video_bytes)

        # Save audio to temp file
        audio_file = os.path.join(temp_dir, "audio.mp3")
        with open(audio_file, "wb") as f:
            f.write(audio_bytes)

        # Output file
        output_file = os.path.join(temp_dir, "output.mp4")

        # Find FFmpeg
        ffmpeg_paths = ['ffmpeg', '/opt/homebrew/bin/ffmpeg', '/usr/local/bin/ffmpeg']
        ffmpeg_cmd = None
        for path in ffmpeg_paths:
            result = subprocess.run(['which', path], capture_output=True, text=True)
            if result.returncode == 0 or os.path.exists(path):
                ffmpeg_cmd = path
                break

        if not ffmpeg_cmd:
            raise FileNotFoundError("ffmpeg not found. Please install FFmpeg: brew install ffmpeg")

        # Build FFmpeg command to combine video and audio
        # -i video: input video file
        # -i audio: input audio file
        # -c:v copy: copy video codec (no re-encoding)
        # -c:a aac: encode audio as AAC
        # -shortest: finish encoding when the shortest input stream ends
        # -map 0:v:0: map video from first input
        # -map 1:a:0: map audio from second input
        cmd = [
            ffmpeg_cmd,
            '-y',  # Overwrite output file
            '-i', video_file,
            '-i', audio_file,
            '-c:v', 'copy',  # Copy video stream (no re-encoding)
            '-c:a', 'aac',  # Encode audio as AAC
            '-b:a', '192k',  # Audio bitrate
            '-shortest',  # Finish when shortest stream ends
            '-map', '0:v:0',  # Map video from first input
            '-map', '1:a:0',  # Map audio from second input
            output_file
        ]

        print(f"[VIDEO AUDIO COMBINER] Running FFmpeg command to combine video and audio...")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"[VIDEO AUDIO COMBINER] FFmpeg error: {result.stderr}")
            return None

        # Read the output video
        with open(output_file, 'rb') as f:
            output_bytes = f.read()

        print(f"[VIDEO AUDIO COMBINER] Successfully combined video and audio, output size: {len(output_bytes)} bytes")

        # Upload to S3
        if not output_key:
            output_key = f"projects/{project_id}/final_video_with_audio.mp4"

        output_s3_url = upload_file_to_s3(
            output_bytes,
            output_key,
            content_type="video/mp4"
        )

        print(f"[VIDEO AUDIO COMBINER] Uploaded combined video to S3: {output_s3_url}")
        return output_s3_url

    except Exception as e:
        print(f"[VIDEO AUDIO COMBINER] Error combining video and audio: {e}")
        import traceback
        print(f"[VIDEO AUDIO COMBINER] Traceback: {traceback.format_exc()}")
        return None
    finally:
        # Clean up temporary files
        for file_path in [video_file, audio_file, output_file]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
        try:
            os.rmdir(temp_dir)
        except:
            pass
