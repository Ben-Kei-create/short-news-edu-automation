# make_short.py
import os
import traceback
import logging
from modules.input_manager import parse_args, get_themes
from modules.theme_selector import filter_duplicate_themes, select_themes_for_batch
from modules.script_generator import generate_script
from modules.image_manager import generate_images
from modules.audio_manager import generate_voice
from modules.bgm_manager import select_bgm
from modules.video_composer import compose_video
from modules.subtitle_generator import generate_subtitles
from modules.thumbnail_generator import generate_thumbnail
from modules.post_log_manager import log_video, post_to_sns
from modules.utils import ensure_folder, load_settings, setup_logging

def setup_directories():
    """必要なフォルダを準備する"""
    ensure_folder("output/videos")
    ensure_folder("output/subtitles")
    ensure_folder("output/thumbnails")
    ensure_folder("output/logs")
    ensure_folder("temp")
    ensure_folder("input/bgm")
    ensure_folder("input/images")
    ensure_folder("input/scripts")

def merge_settings_with_args(settings, args):
    """settings.yamlの内容をコマンドライン引数で上書きする"""
    if args.theme:
        # --themeが指定された場合、テーマを直接settingsに格納
        settings['runtime_themes'] = args.theme
    if args.script_path:
        settings['script']['path'] = args.script_path
    if args.bgm_path:
        settings['bgm']['path'] = args.bgm_path
    
    # --post または --no-post でYouTube投稿設定を上書き
    if args.post:
        settings['youtube']['post_to_youtube'] = True
    if args.no_post:
        settings['youtube']['post_to_youtube'] = False
    
    return settings

def process_single_video(theme, settings):
    """1つのテーマに対して動画を生成する処理"""
    print(f"\n--- テーマ: \"{theme}\" の動画生成を開始します ---")

    try:
        # --- 台本生成 ---
        print("1. 台本を生成中...")
        script_path = settings.get('script', {}).get('path')
        if script_path and os.path.exists(script_path):
            print(f"-> 指定された台本ファイルを使用: {script_path}")
            with open(script_path, 'r', encoding='utf-8') as f:
                script_text = f.read()
        else:
            script_text = generate_script(theme, settings)
        
        if not script_text:
            logging.error(f"台本生成に失敗したため、テーマ「{theme}」の処理を中断します。")
            return

        display_script = script_text.replace('\n', ' ')[:80]
        print(f"-> 生成された台本: {display_script}...")

        # --- 音声生成 ---
        print("2. 音声を生成中...")
        audio_segments_info = generate_voice(script_text, settings)
        if not audio_segments_info:
            logging.error("音声生成に失敗しました。処理を中断します。")
            return
        
        total_duration = sum(seg['duration'] for seg in audio_segments_info)
        print(f"-> 生成された音声長: {total_duration:.2f}秒")

        # --- 画像準備 ---
        print("3. 画像を準備中...")
        images = generate_images(theme, script_text, settings)
        if not images:
            logging.error("画像生成に失敗しました。処理を中断します。")
            return
        print(f"-> 生成された画像数: {len(images)}枚")

        # --- BGM準備 ---
        print("4. BGMを準備中...")
        bgm_file = select_bgm(settings)
        print(f"-> BGMファイル: {bgm_file}")

        # --- 字幕生成 ---
        print("5. 字幕を生成中...")
        subtitle_file = generate_subtitles(theme, audio_segments_info, settings)
        if subtitle_file:
            print(f"-> 字幕ファイル: {subtitle_file}")
        else:
            logging.warning("字幕ファイルの生成に失敗しました。字幕なしで続行します。")

        # --- 動画合成 ---
        print("6. 動画を合成中...")
        video_file = compose_video(theme, images, audio_segments_info, bgm_file, subtitle_file, settings)
        if not video_file:
            logging.error("動画合成に失敗しました。処理を中断します。")
            return
        print(f"-> 動画ファイル: {video_file}")

        # --- サムネイル生成 ---
        print("7. サムネイルを生成中...")
        thumbnail_file = generate_thumbnail(video_file, theme, images, settings)
        if thumbnail_file:
            print(f"-> サムネイルファイル: {thumbnail_file}")

        # --- ログ記録 & SNS投稿 ---
        print("8. ログ記録とSNS投稿...")
        log_video(video_file, theme, settings)
        if settings.get('youtube', {}).get('post_to_youtube', False):
            post_to_sns(video_file, thumbnail_file, theme, script_text, settings)
        else:
            print("-> YouTubeへの投稿はスキップされました。")

    except Exception as e:
        logging.error(f"テーマ「{theme}」の処理中に予期せぬエラーが発生しました。")
        traceback.print_exc()
        return

    print(f"--- テーマ: \"{theme}\" の動画生成が完了しました ---")

def main():
    try:
        # --- 初期設定 ---
        setup_directories()
        args = parse_args()
        settings = load_settings()
        if not settings:
            print("エラー: 設定ファイル(config/settings.yaml)の読み込みに失敗しました。処理を終了します。")
            return
        
        # 引数で設定を上書き
        settings = merge_settings_with_args(settings, args)
        
        # ロギング設定
        setup_logging(settings)

        # --- テーマ取得 ---
        if 'runtime_themes' in settings:
            themes = settings['runtime_themes']
            print(f"{len(themes)}件のテーマが引数で指定されました。")
        else:
            print("RSSフィードからテーマを自動取得します。")
            themes = get_themes(settings)
        
        if not themes:
            print("処理するテーマが見つからないため、終了します。")
            return

        # --- メインループ ---
        print(f"\n>>> 合計{len(themes)}件の動画生成を開始します <<<")
        for i, theme in enumerate(themes):
            process_single_video(theme, settings)
            print(f">>> 進捗: {i + 1}/{len(themes)}件完了 <<<")

        print("\n>>> 全ての動画生成が完了しました <<<")

    except Exception as e:
        print(f"メインプロセスで致命的なエラーが発生しました: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()