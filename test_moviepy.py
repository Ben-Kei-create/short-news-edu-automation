# test_moviepy.py
try:
    from moviepy.video.io.VideoFileClip import VideoFileClip # Corrected import
    from moviepy.audio.io.AudioFileClip import AudioFileClip # Corrected import
    from moviepy.audio.fx.volumex import volumex # Corrected import
    from moviepy.audio.fx.loop import loop # Corrected import
    print("✅ MoviePy imports successful!")
    
    # Test creating a simple clip
    from moviepy.video.VideoClip import ColorClip, CompositeVideoClip # Added CompositeVideoClip
    from moviepy.audio.AudioClip import concatenate_audioclips # Added concatenate_audioclips
    
    clip = ColorClip(size=(640,480), color=(255,0,0)).set_duration(1)
    print("✅ MoviePy functionality test passed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Functionality test failed: {e}")