from moviepy.video.VideoClip import ImageClip
from moviepy import concatenate_videoclips
from moviepy.video.VideoClip import ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

# 画像を順に動画にする（縦1080x1920で揃える）
clips = []
for filename in ["example.png", "example.png"]:  # 本当は違う画像を入れる
    clip = (
        ImageClip(filename)
        .resized(height=1920)    # 高さを1920に
        .with_duration(2)       # 各クリップ2秒
        )
    background_clip = ColorClip(size=(1080, 1920), color=(0, 0, 0)).with_duration(clip.duration)
    clip = CompositeVideoClip([background_clip, clip.with_position("center")])
    clips.append(clip)

# クリップを結合
final_clip = concatenate_videoclips(clips, method="compose")

# 出力
final_clip.write_videofile(
    "output/example_slideshow.mp4",
    fps=50,
    codec="libx264",
    audio_codec="aac",
    ffmpeg_params=["-pix_fmt", "yuv420p"]
)

print("moviepy 2.x 系の複数画像動画テスト完了")