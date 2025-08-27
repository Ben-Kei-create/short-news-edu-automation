import os
import logging

logger = logging.getLogger(__name__)

def select_bgm(settings):
    """
    設定ファイルに基づきBGMファイルを選択する。
    ファイルが存在しない場合は警告を出し、BGMなし（None）を返す。
    """
    bgm_path = settings.get('bgm', {}).get('path')

    if not bgm_path:
        logger.info("設定ファイルでBGMが指定されていないため、BGMなしで動画を生成します。")
        return None

    if os.path.exists(bgm_path):
        logger.info(f"BGMファイルを使用します: {bgm_path}")
        return bgm_path
    else:
        logger.warning(f"指定されたBGMファイル '{bgm_path}' が見つかりません。BGMなしで動画を生成します。")
        return None
