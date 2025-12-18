from moviepy import AudioFileClip, ColorClip
from utils import CancelledError

def convert_mp3_to_mp4(input_path, output_path, logger='bar', resolution=(720, 1280), fps=24):
    """
    Converts an MP3 file to an MP4 video with a black background.
    """
    try:
        # Load audio clip
        audio = AudioFileClip(input_path)
        
        # Create a black background video clip with the same duration as audio
        # In MoviePy 2.x, we use with_duration and with_audio
        video = ColorClip(size=resolution, color=(0, 1, 10)).with_duration(audio.duration)
        video = video.with_audio(audio)
        
        # Write the resulting video to file
        video.write_videofile(
            output_path, 
            fps=fps, 
            codec="libx264", 
            audio_codec="aac",
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
