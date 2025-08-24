import csv
from datetime import datetime
from .youtube_uploader import upload_video

def log_video(video_file, theme, images, style, bgm_file, settings):
    """生成された動画の情報をログファイルに記録する"""
    try:
        log_file = settings['general']['log_file_path']
        with open(log_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([video_file, theme, ";".join(images), style, bgm_file, datetime.now()])
        print(f"ログを記録: {log_file}")
    except Exception as e:
        print(f"エラー: ログの記録中にエラーが発生しました: {e}")

def post_to_sns(video_file, title="", description="", hashtags=None, args=None, settings=None):
    """SNSプラットフォームに動画を投稿する"""
    if not args or not settings:
        print("SNS投稿に必要な引数(args, settings)が不足しています。")
        return

    if args.post_to_youtube:
        print("YouTubeへの投稿を開始します...")
        # ハッシュタグを説明文に追加
        if hashtags:
            description_with_hashtags = description + "\n\n" + " ".join(hashtags)
        else:
            description_with_hashtags = description
        
        upload_video(
            settings=settings,
            video_path=video_file,
            title=title,
            description=description_with_hashtags,
            tags=hashtags,
            privacy_status="private"  # or "public", "unlisted"
        )
    else:
        print("SNSへの投稿は指定されていません。")
