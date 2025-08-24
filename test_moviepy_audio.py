from moviepy.video.VideoClip import ImageClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.VideoClip import ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

# test_moviepy_audio
# 画像から動画を作成（縦1080x1920）
clip = (
    ImageClip("example.png")
    .resized(height=1920)
    .with_duration(5)  # 動画長さは音声より短くてもOK
)
background_clip = ColorClip(size=(1080, 1920), color=(0, 0, 0)).with_duration(clip.duration)
clip = CompositeVideoClip([background_clip, clip.with_position("center")])

# 音声を読み込み（仮に sample.mp3 とする）
audio = AudioFileClip("sample.mp3").subclipped(0, 5)  # 5秒に切る

# 動画に音声をセット
final_clip = clip.with_audio(audio)

# 出力
final_clip.write_videofile(
    "output/example_with_audio.mp4",
    fps=24,
    codec="libx264",
    audio_codec="aac",
    ffmpeg_params=["-pix_fmt", "yuv420p"]
)

print("moviepy 2.x 系の画像＋音声動画テスト完了")
