import csv
import os
from datetime import datetime
from .youtube_uploader import upload_video
import logging

logger = logging.getLogger(__name__)

def log_video(video_file, theme, settings):
    """生成された動画の情報をログファイルに記録する"""
    try:
        log_dir = settings.get('logging', {}).get('directory', 'output/logs')
        os.makedirs(log_dir, exist_ok=True)
        # ログファイル名を video_log.csv などに固定する
        log_file_path = os.path.join(log_dir, "video_production_log.csv")
        
        file_exists = os.path.isfile(log_file_path)
        
        with open(log_file_path, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # ファイルが新規作成された場合、ヘッダーを書き込む
            if not file_exists:
                writer.writerow(["timestamp", "theme", "video_file_path", "audio_engine", "bgm_path"])
            
            # ログデータを書き込む
            writer.writerow([
                datetime.now().isoformat(),
                theme,
                video_file,
                settings.get('audio_engine', 'google'),
                settings.get('bgm', {}).get('path', 'N/A')
            ])
        logger.info(f"動画生成ログを記録しました: {log_file_path}")
    except Exception as e:
        logger.error(f"ログの記録中にエラーが発生しました: {e}", exc_info=True)

def post_to_sns(video_file, thumbnail_file, theme, script_text, settings):
    """SNSプラットフォーム（現在はYouTube）に動画を投稿する"""
    yt_settings = settings.get('youtube', {})
    
    if not yt_settings.get('post_to_youtube', False):
        logger.info("設定でYouTubeへの投稿が無効になっているため、スキップします。")
        return

    logger.info("YouTubeへの投稿を開始します...")

    # --- タイトル、説明、タグを生成 ---
    title = yt_settings.get('title_template', "{theme}").format(theme=theme)
    
    description = yt_settings.get('description_template', "{script}").format(
        theme=theme, 
        script=script_text
    )
    
    tags = yt_settings.get('tags', [])
    # テーマもタグに追加する
    if theme not in tags:
        tags.append(theme)

    try:
        upload_video(
            video_path=video_file,
            thumbnail_path=thumbnail_file,
            title=title,
            description=description,
            tags=tags,
            category_id=yt_settings.get('category_id', '27'),
            privacy_status=yt_settings.get('privacy_status', 'private'),
            settings=settings
        )
    except Exception as e:
        logger.critical(f"YouTubeへのアップロード処理中にエラーが発生しました: {e}", exc_info=True)