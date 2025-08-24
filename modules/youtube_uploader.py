import os
import pickle
import webbrowser
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

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
            # flow.run_local_server() can sometimes fail in non-interactive environments.
            # Using run_console() is a more robust alternative for CLI tools.
            creds = flow.run_console()
        
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def upload_video(settings, video_path, title, description, tags, privacy_status="private"):
    """
    Uploads a video to YouTube.
    """
    try:
        token_path = settings['sns_post']['youtube']['token_path']
        client_secret_path = settings['sns_post']['youtube']['client_secret_path']
    except KeyError:
        print("エラー: settings.yamlにYouTubeのパス設定 ('sns_post.youtube') がありません。")
        return False

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
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "28"  # 24:Entertainment, 28:Science & Technology
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
        import traceback
        traceback.print_exc()
        return False
