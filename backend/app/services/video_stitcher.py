"""
Video stitching utilities using FFmpeg.
"""
import subprocess
import tempfile
import os
from typing import List, Optional
from pathlib import Path

from app.core.s3 import download_file_from_s3, extract_s3_key_from_url, upload_file_to_s3, generate_s3_key


async def stitch_videos_with_transitions(
    video_s3_urls: List[str],
    project_id: str,
    transition_duration: float = 0.5,
) -> Optional[bytes]:
    """
    Stitch multiple videos together with cross-fade transitions using FFmpeg.

    Args:
        video_s3_urls: List of S3 URLs for video files
        project_id: Project ID for generating output S3 key
        transition_duration: Duration of cross-fade transition in seconds (default: 0.5)

    Returns:
        Stitched video bytes if successful, None otherwise
    """
    if not video_s3_urls or len(video_s3_urls) == 0:
        print("[VIDEO STITCHER] No videos to stitch")
        return None
    
    if len(video_s3_urls) == 1:
        # Only one video, just download and return it
        print("[VIDEO STITCHER] Only one video, returning as-is")
        s3_key = extract_s3_key_from_url(video_s3_urls[0])
        if s3_key:
            return download_file_from_s3(s3_key)
        return None
    
    temp_dir = tempfile.mkdtemp()
    temp_video_files = []
    
    try:
        # Download all videos from S3
        print(f"[VIDEO STITCHER] Downloading {len(video_s3_urls)} videos from S3...")
        for i, video_url in enumerate(video_s3_urls):
            s3_key = extract_s3_key_from_url(video_url)
            if not s3_key:
                print(f"[VIDEO STITCHER] Failed to extract S3 key from URL: {video_url}")
                continue
            
            try:
                video_bytes = download_file_from_s3(s3_key)
                if not video_bytes:
                    print(f"[VIDEO STITCHER] Failed to download video from S3: {s3_key}")
                    continue
                
                temp_video_path = os.path.join(temp_dir, f"video_{i}.mp4")
                with open(temp_video_path, 'wb') as f:
                    f.write(video_bytes)
                temp_video_files.append(temp_video_path)
                print(f"[VIDEO STITCHER] Downloaded video {i+1}/{len(video_s3_urls)}: {s3_key}")
            except Exception as e:
                print(f"[VIDEO STITCHER] Error downloading video {i+1} from S3 key {s3_key}: {e}")
                # Continue with other videos instead of failing completely
                continue
        
        if len(temp_video_files) < 2:
            print(f"[VIDEO STITCHER] Need at least 2 videos, got {len(temp_video_files)}")
            return None
        
        # Build FFmpeg filter complex for cross-fade transitions
        output_path = os.path.join(temp_dir, "output.mp4")
        
        # Create filter complex for cross-fade transitions
        # Format: [0:v][1:v]xfade=transition=fade:duration=0.5:offset=VIDEO1_DURATION-0.5[v01];
        #         [v01][2:v]xfade=transition=fade:duration=0.5:offset=VIDEO1_DURATION+VIDEO2_DURATION-0.5[v02];
        #         etc.
        
        # First, get durations of all videos
        # Try to find ffprobe in common locations
        ffprobe_paths = ['ffprobe', '/opt/homebrew/bin/ffprobe', '/usr/local/bin/ffprobe']
        ffprobe_cmd = None
        for path in ffprobe_paths:
            result = subprocess.run(['which', path], capture_output=True, text=True)
            if result.returncode == 0 or os.path.exists(path):
                ffprobe_cmd = path
                break
        
        if not ffprobe_cmd:
            raise FileNotFoundError("ffprobe not found. Please install FFmpeg: brew install ffmpeg")
        
        durations = []
        for video_file in temp_video_files:
            result = subprocess.run(
                [
                    ffprobe_cmd, '-v', 'error', '-show_entries',
                    'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
                    video_file
                ],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                durations.append(duration)
            else:
                print(f"[VIDEO STITCHER] Failed to get duration for {video_file}, using default 6 seconds")
                durations.append(6.0)  # Default duration
        
        # Build filter complex for cross-fade transitions (video and audio)
        video_filter_parts = []
        audio_filter_parts = []
        video_offset = 0.0
        audio_offset = 0.0
        
        # Video cross-fade transitions
        # Format: [0:v][1:v]xfade=transition=fade:duration=0.5:offset=VIDEO0_END-0.5[v01];
        #         [v01][2:v]xfade=transition=fade:duration=0.5:offset=VIDEO0_END+VIDEO1_END-0.5[v02];
        #         etc.
        
        current_video_input = "[0:v]"
        current_audio_input = "[0:a]"
        
        for i in range(len(temp_video_files) - 1):
            # Calculate video offset (cumulative duration minus transition duration)
            video_offset += durations[i] - transition_duration
            
            # Calculate audio offset (same as video for synchronization)
            audio_offset += durations[i] - transition_duration
            
            # Output labels for this step
            video_output_label = f"[v{i+1:02d}]"
            audio_output_label = f"[a{i+1:02d}]"
            
            # Create video cross-fade between current chain and next video
            video_filter_parts.append(
                f"{current_video_input}[{i+1}:v]xfade=transition=fade:duration={transition_duration}:offset={video_offset}{video_output_label}"
            )
            
            # Create audio cross-fade (acrossfade) between current chain and next audio
            # acrossfade automatically applies crossfade near the end of first stream
            # d=duration of crossfade, o=overlap (1=yes, 0=no)
            audio_filter_parts.append(
                f"{current_audio_input}[{i+1}:a]acrossfade=d={transition_duration}:o=1{audio_output_label}"
            )
            
            # Next iteration uses these outputs as inputs
            current_video_input = video_output_label
            current_audio_input = audio_output_label
        
        # Combine video and audio filter parts
        all_filter_parts = video_filter_parts + audio_filter_parts
        filter_complex = ";".join(all_filter_parts)
        final_video_output = current_video_input  # Last video output label
        final_audio_output = current_audio_input  # Last audio output label
        
        # Try to find ffmpeg in common locations
        ffmpeg_paths = ['ffmpeg', '/opt/homebrew/bin/ffmpeg', '/usr/local/bin/ffmpeg']
        ffmpeg_cmd = None
        for path in ffmpeg_paths:
            result = subprocess.run(['which', path], capture_output=True, text=True)
            if result.returncode == 0 or os.path.exists(path):
                ffmpeg_cmd = path
                break
        
        if not ffmpeg_cmd:
            raise FileNotFoundError("ffmpeg not found. Please install FFmpeg: brew install ffmpeg")
        
        # Build FFmpeg command
        input_args = []
        for video_file in temp_video_files:
            input_args.extend(['-i', video_file])
        
        cmd = [
            ffmpeg_cmd,
            '-y',  # Overwrite output file
            *input_args,
            '-filter_complex', filter_complex,
            '-map', final_video_output,  # Map video output
            '-map', final_audio_output,  # Map audio output
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac',  # Audio codec
            '-b:a', '192k',  # Audio bitrate
            output_path
        ]
        
        print(f"[VIDEO STITCHER] Running FFmpeg command...")
        print(f"[VIDEO STITCHER] Filter complex: {filter_complex}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"[VIDEO STITCHER] FFmpeg error: {result.stderr}")
            return None
        
        # Read the output video
        with open(output_path, 'rb') as f:
            output_bytes = f.read()
        
        print(f"[VIDEO STITCHER] Successfully stitched {len(temp_video_files)} videos, output size: {len(output_bytes)} bytes")
        return output_bytes
        
    except Exception as e:
        print(f"[VIDEO STITCHER] Error stitching videos: {e}")
        import traceback
        print(f"[VIDEO STITCHER] Traceback: {traceback.format_exc()}")
        return None
    finally:
        # Clean up temporary files
        for video_file in temp_video_files:
            try:
                if os.path.exists(video_file):
                    os.remove(video_file)
            except Exception as e:
                print(f"[VIDEO STITCHER] Failed to remove temp file {video_file}: {e}")
        
        try:
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except Exception as e:
            print(f"[VIDEO STITCHER] Failed to remove temp dir {temp_dir}: {e}")
