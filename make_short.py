# make_short.py
from modules.input_manager import parse_args, get_themes
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

def setup_directories():
    """必要なフォルダを準備する"""
    ensure_folder("output/videos")
    ensure_folder("output/subtitles")
    ensure_folder("output/thumbnails")
    ensure_folder("output/logs")
    ensure_folder("temp")

def process_single_video(theme, args):
    """1つのテーマに対して動画を生成する処理"""
    print(f"\n--- テーマ: \"{theme}\" の動画生成を開始します ---")

    # --- 台本生成 ---
    print("1. 台本を生成中...")
    script_text = generate_script(theme)
    display_script_text = script_text[:50].replace('\n', ' ')
    print(f"-> 生成された台本: {display_script_text}...")

    # --- 画像準備 ---
    print("2. 画像を準備中...")
    manual_images = load_manual_images(args.manual_images)
    num_images_needed = 12 # 1枚5秒 x 12枚 = 60秒
    generated_images = generate_images(
        theme=theme,
        style=args.style,
        num=num_images_needed - len(manual_images),
        use_sd_api=args.use_sd_api,
        sd_model=args.sd_model,
        lora_model=args.lora_model,
        lora_weight=args.lora_weight
    )
    images = manual_images + generated_images
    print(f"-> 使用する画像: {images}")

    # --- 音声生成 ---
    print("3. 音声を生成中...")
    audio_segments_info = generate_voice(script_text) # Modified
    if not audio_segments_info:
        print("エラー: 音声生成に失敗しました。")
        return

    # --- 音声長チェック ---
    total_duration = sum(segment['duration'] for segment in audio_segments_info if segment['duration'] is not None)
    print(f"-> 生成された音声の合計時間: {total_duration:.2f}秒")
    if total_duration < 58: # 少しマージンを持たせる
        print(f"エラー: 生成された音声が60秒に満たないため ({total_duration:.2f}秒)、処理を中断します。台本を長くしてください。")
        return
    
    print(f"-> 音声セグメント情報: {len(audio_segments_info)}個のセグメント") # Modified

    # --- BGM準備 ---
    print("4. BGMを準備中...")
    bgm_file = select_bgm(args.bgm_path)
    print(f"-> BGMファイル: {bgm_file}")

    # --- 字幕生成 ---
    print("5. 字幕を生成中...")
    subtitle_file = generate_subtitles(theme, audio_segments_info)
    if not subtitle_file:
        print("警告: 字幕ファイルの生成に失敗しました。字幕なしで処理を続行します。")
    else:
        print(f"-> 字幕ファイル: {subtitle_file}")

    # --- 動画合成 ---
    print("6. 動画を合成中...")
    video_file = compose_video(
        theme=theme, 
        images=images, 
        audio_segments_info=audio_segments_info, 
        bgm_file=bgm_file, 
        subtitle_file=subtitle_file,
        font_filename=args.font
    )
    if not video_file:
        print("エラー: 動画合成に失敗しました。このテーマの処理を中断します。")
        return
    print(f"-> 動画ファイル: {video_file}")

    # --- サムネイル生成 ---
    print("7. サムネイルを生成中...")
    thumbnail_file = generate_thumbnail(theme, images)
    print(f"-> サムネイルファイル: {thumbnail_file}")

    # --- ログ記録 ---
    print("8. ログを記録中...")
    log_video(video_file, theme, images, args.style, bgm_file)

    # --- SNS投稿 ---
    print("9. SNSに投稿中...")
    post_to_sns(video_file, title=theme, description=script_text, hashtags=["#しくじり先生", "#短編動画"])
    
    print(f"--- テーマ: \"{theme}\" の動画生成が完了しました ---")


def main():
    # --- 初期設定 ---
    setup_directories()
    args = parse_args()

    # --- テーマ取得 ---
    themes = get_themes(args)
    if not themes:
        print("処理するテーマが見つからないため、終了します。")
        return

    # --- メインループ ---
    print(f"\n>>> 合計{len(themes)}件の動画生成を開始します <<<")
    for i, theme in enumerate(themes):
        process_single_video(theme, args)
        print(f">>> 進捗: {i + 1}/{len(themes)}件完了 <<<")

    print("\nすべての動画生成が完了しました。お疲れ様でした！")

if __name__ == "__main__":
    main()
