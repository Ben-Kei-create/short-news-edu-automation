import os
import pickle
import webbrowser
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import traceback

# This scope allows for full access to the user's YouTube account.
YOUTUBE_UPLOAD_SCOPE = ["https://www.googleapis.com/auth/youtube.upload"]

def get_credentials(token_path, client_secret_path):
    """
    Handles OAuth 2.0 authentication.
    Loads existing credentials or initiates the OAuth 2.0 flow.
    """
    creds = None
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(client_secret_path):
                print(f"エラー: クライアントシークレットファイルが見つかりません: {client_secret_path}")
                print("Google Cloud Consoleからダウンロードし、プロジェクトルートに配置してください。")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secret_path, YOUTUBE_UPLOAD_SCOPE)
            creds = flow.run_console()
        
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

# upload_video 関数の引数を変更し、settingsから情報を取得するようにする
def upload_video(video_path, theme, script_text, settings):
    """
    Uploads a video to YouTube using settings from config/settings.yaml.
    """
    youtube_settings = settings.get('youtube', {})
    
    # settingsからタイトル、説明、タグ、カテゴリ、プライバシー設定を取得
    title_prefix = youtube_settings.get('default_title_prefix', '')
    description_suffix = youtube_settings.get('default_description_suffix', '')
    default_tags = youtube_settings.get('default_tags', [])
    category_id = youtube_settings.get('category_id', '28') # Default to Science & Technology
    privacy_status = youtube_settings.get('privacy_status', 'private')

    # タイトルと説明文を生成 (themeとscript_textを使用)
    # ここでより高度なタイトル/説明文生成ロジックを実装可能
    video_title = f"{title_prefix}{theme}"
    video_description = f"{script_text}\n\n{description_suffix}"
    video_tags = default_tags # 必要に応じてthemeやscript_textからタグを生成することも可能

    # token_pathとclient_secret_pathはsettings.yamlに直接記述しない方が良いが、
    # 現状のコードに合わせて一時的にここに記述。将来的には環境変数などから取得すべき。
    # または、settings.yamlにパスを記述し、それを読み込む。
    # 今回は、settings.yamlにパスを記述する前提で修正。
    token_path = "youtube_token.json" # 固定値またはsettingsから取得
    client_secret_path = "client_secret.json" # 固定値またはsettingsから取得

    if not os.path.exists(video_path):
        print(f"エラー: アップロードする動画ファイルが見つかりません: {video_path}")
        return False

    credentials = get_credentials(token_path, client_secret_path)
    if not credentials:
        print("エラー: YouTubeの認証に失敗しました。")
        return False

    youtube = build("youtube", "v3", credentials=credentials)

    body = {
        "snippet": {
            "title": video_title,
            "description": video_description,
            "tags": video_tags,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        }
    }

    try:
        print(f"  - YouTubeへのアップロードを開始します: {video_path}")
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        
        request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"  - アップロード進捗: {int(status.progress() * 100)}%")
        
        print(f"アップロード完了！ 動画ID: {response.get('id')}")
        print(f"動画リンク: https://www.youtube.com/watch?v={response.get('id')}")
        return True

    except Exception as e:
        print(f"エラー: YouTubeへのアップロード中にエラーが発生しました: {e}")
        traceback.print_exc()
        return False

# post_to_sns 関数は make_short.py から呼び出されるため、
# ここでは upload_video を呼び出すように修正する。
# make_short.py 側で post_to_sns の引数を調整する必要がある。
def post_to_sns(video_file, title, description, hashtags, args, settings):
    """
    SNSへの投稿を処理する。現在はYouTubeのみ対応。
    """
    if args.post_to_youtube:
        print("  - YouTubeに投稿します。")
        # upload_video に必要な引数を渡す
        return upload_video(video_file, title, description, settings)
    else:
        print("  - YouTubeへの投稿はスキップされました。")
        return False