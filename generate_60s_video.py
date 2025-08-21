import os
import glob
import sys
from moviepy.video.VideoClip import ImageClip, ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.io.VideoFileClip import VideoFileClip

# --- 定数 ---
INPUT_DIR = "input"
OUTPUT_DIR = "output"
TARGET_DURATION = 60
VIDEO_WIDTH, VIDEO_HEIGHT = 1080, 1920
SUPPORTED_IMAGE_EXT = ('.png', '.jpg', '.jpeg')
SUPPORTED_AUDIO_EXT = ('.mp4', '.mp3', '.wav', '.m4a')

# --- ディレクトリ準備 ---
# 出力ディレクトリ
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# 入力ディレクトリ
if not os.path.exists(INPUT_DIR):
    print(f"入力ディレクトリ '{INPUT_DIR}' が存在しないため作成しました。")
    print(f"'{INPUT_DIR}' フォルダに、動画に使用する画像ファイルと音声ファイルを1つずつ入れてから、再度実行してください。")
    sys.exit() # スクリプトを終了

# --- 入力ファイル検索 ---
print(f"'{INPUT_DIR}' フォルダから入力ファイルを検索します...")
image_files = []
audio_files = []

# 大文字小文字を区別せずにファイルを検索
for ext in SUPPORTED_IMAGE_EXT:
    image_files.extend(glob.glob(os.path.join(INPUT_DIR, f"*[.{ext[1:].lower()}]")))
    image_files.extend(glob.glob(os.path.join(INPUT_DIR, f"*[.{ext[1:].upper()}]")))

for ext in SUPPORTED_AUDIO_EXT:
    audio_files.extend(glob.glob(os.path.join(INPUT_DIR, f"*[.{ext[1:].lower()}]")))
    audio_files.extend(glob.glob(os.path.join(INPUT_DIR, f"*[.{ext[1:].upper()}]")))

# 重複を除去し、名前順でソート
image_files = sorted(list(set(image_files)))
audio_files = sorted(list(set(audio_files)))

# ファイル存在チェック
if not image_files:
    print(f"エラー: '{INPUT_DIR}' に画像ファイルが見つかりません。")
    print(f"対応形式: {', '.join(SUPPORTED_IMAGE_EXT)}")
    sys.exit()

if not audio_files:
    print(f"エラー: '{INPUT_DIR}' に音声ファイルが見つかりません。")
    print(f"対応形式: {', '.join(SUPPORTED_AUDIO_EXT)}")
    sys.exit()

# 使用するファイルを決定（ソートして最初に見つかったものを使用）
input_image_path = image_files[0]
input_audio_path = audio_files[0]
print(f"-> 使用する画像: {input_image_path}")
print(f"-> 使用する音声: {input_audio_path}")


# --- 動画生成メイン処理 ---
print("\n音声ファイルを読み込んでいます...")
audio_clip = VideoFileClip(input_audio_path).audio

if audio_clip.duration < TARGET_DURATION:
    raise ValueError(
        f"バックグラウンド音声の長さが不足しています: "
        f"{audio_clip.duration:.2f}秒 (必要: {TARGET_DURATION}秒以上)"
    )

print(f"BGMが{audio_clip.duration:.2f}秒 のため、冒頭{TARGET_DURATION}秒を使用します。")

# 画像から縦長動画作成
image_clip = ImageClip(input_image_path).resized(height=VIDEO_HEIGHT).with_duration(TARGET_DURATION)

# 黒背景作成＋画像を中央に配置
background_clip = ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=(0, 0, 0)).with_duration(TARGET_DURATION)
final_clip = CompositeVideoClip([background_clip, image_clip.with_position("center")])

# 動画に音声をセット（冒頭60秒）
final_clip = final_clip.with_audio(audio_clip.subclipped(0, TARGET_DURATION))

# 出力ファイル名を生成
base_name = os.path.splitext(os.path.basename(input_image_path))[0]
output_video_path = os.path.join(OUTPUT_DIR, f"{base_name}_short_video.mp4")

print("\n動画を生成しています...")
final_clip.write_videofile(
    output_video_path,
    fps=24,
    codec="libx264",
    audio_codec="aac",
    ffmpeg_params=["-pix_fmt", "yuv420p"]
)

print(f"\n作成完了: {output_video_path}")
