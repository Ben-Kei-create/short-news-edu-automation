# make_short.py
from modules.input_manager import parse_args, get_theme
from modules.theme_selector import filter_duplicate_themes, select_themes_for_batch
from modules.script_generator import generate_script
from modules.image_manager import load_manual_images, generate_images
from modules.audio_manager import generate_voice
from modules.bgm_manager import select_bgm
from modules.video_composer import compose_video
from modules.subtitle_generator import generate_subtitles
from modules.thumbnail_generator import generate_thumbnail
from modules.post_log_manager import log_video, post_to_sns
from modules.utils import ensure_folder

import os

# --- フォルダ準備 ---
ensure_folder("output/videos")
ensure_folder("output/subtitles")
ensure_folder("output/thumbnails")
ensure_folder("output/logs")
ensure_folder("temp")

def main():
    # --- 引数解析 ---
    args = parse_args()

    # --- テーマ取得 ---
    theme = get_theme(args)
    print(f"選択されたテーマ: {theme}")

    # --- 台本生成 ---
    script_text = generate_script(theme)
    print(f"生成された台本: {script_text[:50]}...")

    # --- 画像準備 ---
    manual_images = load_manual_images(args.manual_images)
    num_images_needed = 5  # 仮: 60秒動画なら5枚スライド
    generated_images = generate_images(theme, args.style, num_images_needed - len(manual_images))
    images = manual_images + generated_images
    print(f"使用する画像: {images}")

    # --- 音声生成 ---
    audio_file = generate_voice(script_text)
    print(f"音声ファイル: {audio_file}")

    # --- BGM準備 ---
    bgm_file = select_bgm(args.bgm_path)
    print(f"BGMファイル: {bgm_file}")

    # --- 動画合成 ---
    video_file = compose_video(images, audio_file, bgm_file)
    print(f"動画ファイル: {video_file}")

    # --- 字幕生成 ---
    subtitle_file = generate_subtitles(script_text, audio_file)
    print(f"字幕ファイル: {subtitle_file}")

    # --- サムネイル生成 ---
    thumbnail_file = generate_thumbnail(images)
    print(f"サムネイルファイル: {thumbnail_file}")

    # --- ログ記録 ---
    log_video(video_file, theme, images, args.style, bgm_file)

    # --- SNS投稿 ---
    post_to_sns(video_file, title=theme, description=script_text, hashtags=["#しくじり先生", "#短編動画"])

if __name__ == "__main__":
    main()