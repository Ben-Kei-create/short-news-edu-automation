from moviepy.video.VideoClip import ImageClip, ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.fx.all import audio_loop

VIDEO_DURATION = 60  # 60秒
VIDEO_WIDTH, VIDEO_HEIGHT = 1080, 1920

# sample.mp4 から音声を取得
audio_clip = VideoFileClip("sample.mp4").audio

# 音声が1分未満ならループさせる
if audio_clip.duration < VIDEO_DURATION:
    print(f"音声が{VIDEO_DURATION}秒未満のため、ループ処理を実行します。")
    audio_clip = audio_loop(audio_clip, duration=VIDEO_DURATION)

# 画像から縦長動画作成
clip = ImageClip("example.png").resized(height=VIDEO_HEIGHT).with_duration(VIDEO_DURATION)

# 黒背景作成＋画像を中央に配置
background_clip = ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=(0, 0, 0)).with_duration(VIDEO_DURATION)
clip = CompositeVideoClip([background_clip, clip.with_position("center")])

# 動画に音声をセット（1分間に切り出し）
final_clip = clip.with_audio(audio_clip.subclipped(0, VIDEO_DURATION))

# 出力
final_clip.write_videofile(
    "output/example_with_looped_audio.mp4",
    fps=24,
    codec="libx264",
    audio_codec="aac",
    ffmpeg_params=["-pix_fmt", "yuv420p"]
)

print("縦長動画＋ループ音声付き（1分ショート）作成 完了")
