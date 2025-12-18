from moviepy import AudioFileClip, ColorClip
from utils import CancelledError

def convert_mp3_to_mp4(input_path, output_path, logger='bar', resolution=(240, 320), fps=1):
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
            fps=fps, 
            codec="libx264", 
            audio_codec="aac",
            preset="ultrafast",
            threads=1, # Render Free tier is limited
            ffmpeg_params=[
                "-pix_fmt", "yuv420p", 
                "-tune", "stillimage",
                "-crf", "28" # Slightly lower quality for much faster speed
            ],
            logger=logger
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
