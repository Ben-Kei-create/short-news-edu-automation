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
from modules.utils import ensure_folder, load_settings # load_settings を追加

import os
import traceback # 追加

def setup_directories():
    """必要なフォルダを準備する"""
    ensure_folder("output/videos")
    ensure_folder("output/subtitles")
    ensure_folder("output/thumbnails")
    ensure_folder("output/logs")
    ensure_folder("temp")
    ensure_folder("input/fonts")

# process_single_video 関数の引数に settings を追加
def process_single_video(theme, args, settings):
    """1つのテーマに対して動画を生成する処理"""
    print(f"\n--- テーマ: \"{theme}\" の動画生成を開始します ---")

    try:
        # --- 台本生成 ---
        print("1. 台本を生成中...")
        # generate_script 関数に settings を渡す
        script_text = generate_script(theme, settings)
        display_script_text = script_text[:50].replace('\n', ' ')
        print(f"-> 生成された台本: {display_script_text}...")
    except Exception as e:
        print(f"エラー: 台本生成中に問題が発生しました: {e}")
        traceback.print_exc()
        return

    try:
        # --- 画像準備 ---
        print("2. 画像を準備中...")
        manual_images = load_manual_images(args.manual_images)
        # num_images_needed を settings から取得
        num_images_needed = settings['general']['num_images_needed']
        generated_images = generate_images(
            theme=theme,
            style=args.style,
            num=num_images_needed - len(manual_images),
            use_sd_api=args.use_sd_api,
            sd_model=args.sd_model,
            lora_model=args.lora_model,
            lora_weight=args.lora_weight,
            settings=settings # settings を渡す
        )
        images = manual_images + generated_images
        print(f"-> 使用する画像: {images}")
    except Exception as e:
        print(f"エラー: 画像準備中に問題が発生しました: {e}")
        traceback.print_exc()
        return

    try:
        # --- 音声生成 ---
        print("3. 音声を生成中...")
        # generate_voice 関数に settings を渡す
        audio_segments_info = generate_voice(script_text, settings)
        if not audio_segments_info:
            print("エラー: 音声生成に失敗しました。")
            return
    except Exception as e:
        print(f"エラー: 音声生成中に問題が発生しました: {e}")
        traceback.print_exc()
        return

    try:
        # --- 音声長チェック ---
        total_duration = sum(segment['duration'] for segment in audio_segments_info if segment['duration'] is not None)
        print(f"-> 生成された音声の合計時間: {total_duration:.2f}秒")
        # min_duration_seconds を settings から取得
        min_duration_seconds = settings['google_tts']['min_duration_seconds']
        if total_duration < min_duration_seconds:
            print(f"エラー: 生成された音声が60秒に満たないため ({total_duration:.2f}秒)、処理を中断します。台本を長くしてください。")
            return
        
        print(f"-> 音声セグメント情報: {len(audio_segments_info)}個のセグメント")
    except Exception as e:
        print(f"エラー: 音声長チェック中に問題が発生しました: {e}")
        traceback.print_exc()
        return

    try:
        # --- BGM準備 ---
        print("4. BGMを準備中...")
        # select_bgm 関数に settings を渡す
        bgm_file = select_bgm(args.bgm_path, settings)
        print(f"-> BGMファイル: {bgm_file}")
    except Exception as e:
        print(f"エラー: BGM準備中に問題が発生しました: {e}")
        traceback.print_exc()
        return

    try:
        # --- 字幕生成 ---
        print("5. 字幕を生成中...")
        # generate_subtitles 関数に settings を渡す (現時点では不要だが、将来のために引数に追加)
        subtitle_file = generate_subtitles(theme, audio_segments_info)
        if not subtitle_file:
            print("警告: 字幕ファイルの生成に失敗しました。字幕なしで処理を続行します。")
        else:
            print(f"-> 字幕ファイル: {subtitle_file}")
    except Exception as e:
        print(f"エラー: 字幕生成中に問題が発生しました: {e}")
        traceback.print_exc()
        subtitle_file = None

    try:
        # --- 動画合成 ---
        print("6. 動画を合成中...")
        # compose_video 関数に settings を渡す
        video_file = compose_video(
            theme=theme,
            images=images,
            audio_segments_info=audio_segments_info,
            bgm_path=bgm_file,
            subtitle_file=subtitle_file,
            font_filename=args.font,
            image_duration=args.image_duration,
            settings=settings # settings を渡す
        )
        if not video_file:
            print("エラー: 動画合成に失敗しました。このテーマの処理を中断します。")
            return
        print(f"-> 動画ファイル: {video_file}")
    except Exception as e:
        print(f"エラー: 動画合成中に問題が発生しました: {e}")
        traceback.print_exc()
        return

    try:
        # --- サムネイル生成 ---
        print("7. サムネイルを生成中...")
        # generate_thumbnail 関数に settings を渡す
        thumbnail_file = generate_thumbnail(theme, images, settings)
        print(f"-> サムネイルファイル: {thumbnail_file}")
    except Exception as e:
        print(f"エラー: サムネイル生成中に問題が発生しました: {e}")
        traceback.print_exc()

    try:
        # --- ログ記録 ---
        print("8. ログを記録中...")
        # log_video 関数に settings を渡す
        log_video(video_file, theme, images, args.style, bgm_file, settings)
    except Exception as e:
        print(f"エラー: ログ記録中に問題が発生しました: {e}")
        traceback.print_exc()

    try:
        # --- SNS投稿 ---
        print("9. SNSに投稿中...")
        post_to_sns(video_file, title=theme, description=script_text, hashtags=["#しくじり先生", "#短編動画"])
    except Exception as e:
        print(f"エラー: SNS投稿中に問題が発生しました: {e}")
        traceback.print_exc()
    
    print(f"--- テーマ: \"{theme}\" の動画生成が完了しました ---")


def main():
    try:
        # --- 初期設定 ---
        setup_directories()
        args = parse_args()
        settings = load_settings() # settings を読み込む
        if not settings: # settings の読み込みに失敗した場合
            print("設定ファイルの読み込みに失敗しました。処理を終了します。")
            return

        # --- テーマ取得 ---
        themes = get_themes(args)
        if not themes:
            print("処理するテーマが見つからないため、終了します。")
            return

        # --- メインループ ---
        print(f"\n>>> 合計{len(themes)}件の動画生成を開始します <<<")
        for i, theme in enumerate(themes):
            # process_single_video 関数に settings を渡す
            process_single_video(theme, args, settings)
            print(f">>> 進捗: {i + 1}/{len(themes)}件完了 <<<")

        print("\n>>> 全ての動画生成が完了しました <<<")

    except Exception as e:
        print(f"メインプロセスでエラーが発生しました: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
