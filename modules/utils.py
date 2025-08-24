# modules/utils.py
import os
import yaml

def ensure_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def load_settings(config_path="config/settings.yaml"):
    """
    設定ファイルを読み込む。
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            settings = yaml.safe_load(f)
        return settings
    except FileNotFoundError:
        print(f"エラー: 設定ファイル '{config_path}' が見つかりません。")
        return None
    except yaml.YAMLError as e:
        print(f"エラー: 設定ファイル '{config_path}' の解析に失敗しました: {e}")
        return None