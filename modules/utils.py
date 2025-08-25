import os
import yaml
import logging
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv # 追加

def ensure_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def load_settings(config_path="config/settings.yaml"):
    """
    設定ファイルを読み込む。
    """
    # .envファイルから環境変数をロード
    load_dotenv()

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            settings = yaml.safe_load(f)

        # APIキーを環境変数から上書き
        if 'api_keys' in settings:
            for key, value in settings['api_keys'].items():
                env_var_name = f"{key.upper()}_API_KEY"
                if key == "google_custom_search_cx":
                    env_var_name = "GOOGLE_CUSTOM_SEARCH_CX"
                settings['api_keys'][key] = os.getenv(env_var_name, value)

        return settings
    except FileNotFoundError:
        logging.error(f"設定ファイル '{config_path}' が見つかりません。")
        return None
    except yaml.YAMLError as e:
        logging.error(f"設定ファイル '{config_path}' の解析に失敗しました: {e}")
        return None

def setup_logging(settings):
    """
    ロギングを設定する。
    """
    log_level_str = settings.get('logging', {}).get('level', 'INFO').upper()
    log_file_path = settings.get('logging', {}).get('log_file_path', 'output/logs/app.log')

    # ログレベルの変換
    log_level = getattr(logging, log_level_str, logging.INFO)

    # ログディレクトリの作成
    log_dir = os.path.dirname(log_file_path)
    ensure_folder(log_dir)

    # ルートロガーを取得
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # 既存のハンドラをクリア (複数回呼び出し対策)
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)

    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイルハンドラ (日付ローテーション)
    file_handler = TimedRotatingFileHandler(
        log_file_path,
        when="midnight", # 毎日午前0時にローテーション
        interval=1,
        backupCount=7, # 7日分のログを保持
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logging.info("ロギングが設定されました。")
