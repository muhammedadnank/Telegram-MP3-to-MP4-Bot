from moviepy import AudioFileClip, ColorClip

class CancelledError(Exception):
    """Custom exception to handle task cancellation."""
    pass

def convert_mp3_to_mp4(input_path, output_path, logger='bar', resolution=(144, 256), fps=1):
    """
    Converts an MP3 file to an MP4 video with a black background.
    Optimized for extremely fast processing (1 fps, low res).
    """
    try:
        # Load audio clip
        audio = AudioFileClip(input_path)
        
        # Create a black background video clip with the same duration as audio
        # Using 1 FPS drastically reduces encoding time for black-screen videos
        video = ColorClip(size=resolution, color=(0, 0, 0)).with_duration(audio.duration)
        video = video.with_audio(audio)
        
        # Write the resulting video to file
        print(f"DEBUG: Starting ultra-fast write_videofile for {output_path}")
        video.write_videofile(
            output_path, 
            fps=2, # 2 FPS is safer than 1 for many muxers
            codec="libx264", 
            audio_codec="aac",
            audio_bitrate="128k", # Fixed bitrate for faster encoding
            preset="ultrafast",
            threads=1, 
            ffmpeg_params=[
                "-pix_fmt", "yuv420p", 
                "-tune", "stillimage",
                "-movflags", "+faststart", # Allow playing while downloading
                "-shortest" # Ensure video ends with audio
            ],
            logger=logger,
            bitrate="50k" # Extremely low video bitrate since it's just black
        )
        
        # Close clips to release resources
        audio.close()
        video.close()
        return True
    except CancelledError:
        # Propagate cancellation
        raise
    except Exception as e:
        print(f"Error during conversion: {e}")
        return False
