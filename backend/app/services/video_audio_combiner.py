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
    audio_bytes: Optional[bytes] = None,
    project_id: str = "",
    output_key: Optional[str] = None,
    audio_mode: str = "overwrite",
    audio_s3_url: Optional[str] = None,
) -> Optional[str]:
    """
    Combine video and audio using FFmpeg.

    Args:
        video_s3_url: S3 URL of the video file
        audio_bytes: Audio bytes to combine with video (optional if audio_s3_url is provided)
        project_id: Project ID for generating output S3 key
        output_key: Optional custom S3 key for output (defaults to final_video_with_audio.mp4)
        audio_mode: "overwrite" to replace existing audio, "overlay" to mix with existing audio
        audio_s3_url: Optional S3 URL of the audio file (used if audio_bytes is not provided)

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

        # Get audio bytes (either from parameter or download from S3)
        if audio_bytes:
            audio_data = audio_bytes
        elif audio_s3_url:
            audio_s3_key = extract_s3_key_from_url(audio_s3_url)
            if not audio_s3_key:
                print("[VIDEO AUDIO COMBINER] Failed to extract S3 key from audio URL")
                return None
            audio_data = download_file_from_s3(audio_s3_key)
            if not audio_data:
                print("[VIDEO AUDIO COMBINER] Failed to download audio from S3")
                return None
        else:
            print("[VIDEO AUDIO COMBINER] Either audio_bytes or audio_s3_url must be provided")
            return None

        # Save audio to temp file
        audio_file = os.path.join(temp_dir, "audio.mp3")
        with open(audio_file, "wb") as f:
            f.write(audio_data)

        # Output file
        output_file = os.path.join(temp_dir, "output.mp4")

        # Find FFmpeg and ffprobe
        ffmpeg_paths = ['ffmpeg', '/opt/homebrew/bin/ffmpeg', '/usr/local/bin/ffmpeg']
        ffprobe_paths = ['ffprobe', '/opt/homebrew/bin/ffprobe', '/usr/local/bin/ffprobe']
        ffmpeg_cmd = None
        ffprobe_cmd = None
        
        for path in ffmpeg_paths:
            result = subprocess.run(['which', path], capture_output=True, text=True)
            if result.returncode == 0 or os.path.exists(path):
                ffmpeg_cmd = path
                break
        
        for path in ffprobe_paths:
            result = subprocess.run(['which', path], capture_output=True, text=True)
            if result.returncode == 0 or os.path.exists(path):
                ffprobe_cmd = path
                break

        if not ffmpeg_cmd:
            raise FileNotFoundError("ffmpeg not found. Please install FFmpeg: brew install ffmpeg")
        if not ffprobe_cmd:
            raise FileNotFoundError("ffprobe not found. Please install FFmpeg: brew install ffmpeg")

        # Get video and audio durations
        def get_duration(file_path: str) -> float:
            """Get duration of a media file in seconds."""
            try:
                result = subprocess.run(
                    [ffprobe_cmd, '-v', 'error', '-show_entries',
                     'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
                     file_path],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return float(result.stdout.strip())
            except:
                pass
            return 0.0

        video_duration = get_duration(video_file)
        audio_duration = get_duration(audio_file)
        
        print(f"[VIDEO AUDIO COMBINER] Video duration: {video_duration}s, Audio duration: {audio_duration}s")

        # Build FFmpeg command based on audio mode
        if audio_mode == "overlay":
            # Overlay mode: mix existing video audio with new BGM audio
            # Extract video audio, mix with BGM, then combine back
            # Use amix filter to mix audio tracks
            cmd = [
                ffmpeg_cmd,
                '-y',  # Overwrite output file
                '-i', video_file,
                '-i', audio_file,
                '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2[a]',
                '-c:v', 'copy',  # Copy video stream (no re-encoding)
                '-map', '0:v:0',  # Map video from first input
                '-map', '[a]',  # Map mixed audio
                '-c:a', 'aac',  # Encode audio as AAC
                '-b:a', '192k',  # Audio bitrate
                output_file
            ]
        else:
            # Overwrite mode: replace existing audio with new audio
            # If audio is shorter than video, pad it with silence to match video length
            if audio_duration > 0 and video_duration > 0 and audio_duration < video_duration:
                print(f"[VIDEO AUDIO COMBINER] Audio ({audio_duration}s) is shorter than video ({video_duration}s), padding with silence")
                # Use apad filter to pad audio with silence to match video duration
                cmd = [
                    ffmpeg_cmd,
                    '-y',  # Overwrite output file
                    '-i', video_file,
                    '-i', audio_file,
                    '-filter_complex', f'[1:a]apad=whole_dur={video_duration}[padded_audio]',
                    '-c:v', 'copy',  # Copy video stream (no re-encoding)
                    '-map', '0:v:0',  # Map video from first input
                    '-map', '[padded_audio]',  # Map padded audio
                    '-c:a', 'aac',  # Encode audio as AAC
                    '-b:a', '192k',  # Audio bitrate
                    output_file
                ]
            else:
                # Audio is longer or equal to video, or durations couldn't be determined
                # Use shortest to avoid issues, or if audio >= video, just map normally
                if audio_duration > 0 and video_duration > 0 and audio_duration >= video_duration:
                    # Audio is longer, use shortest to match video length
                    cmd = [
                        ffmpeg_cmd,
                        '-y',  # Overwrite output file
                        '-i', video_file,
                        '-i', audio_file,
                        '-c:v', 'copy',  # Copy video stream (no re-encoding)
                        '-c:a', 'aac',  # Encode audio as AAC
                        '-b:a', '192k',  # Audio bitrate
                        '-shortest',  # Finish when shortest stream (video) ends
                        '-map', '0:v:0',  # Map video from first input
                        '-map', '1:a:0',  # Map audio from second input
                        output_file
                    ]
                else:
                    # Fallback: use shortest if durations couldn't be determined
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
