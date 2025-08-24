import os
import logging # 追加

logger = logging.getLogger(__name__) # ロガーを取得

# select_bgm 関数の引数に settings を追加
def select_bgm(bgm_path=None, settings=None):
    """
    BGMファイルを選択する。指定がなければデフォルトのBGMを探す。
    """
    if bgm_path:
        if os.path.exists(bgm_path):
            logger.info(f"指定されたBGMファイルを使用します: {bgm_path}")
            return bgm_path
        else:
            logger.warning(f"指定されたBGMファイル '{bgm_path}' が見つかりません。デフォルトBGMを探します。")

    # デフォルトBGMの候補 (優先順位順) を settings から取得
    default_bgm_candidates = settings.get('bgm', {}).get('default_candidates', [])

    for candidate in default_bgm_candidates:
        if os.path.exists(candidate):
            logger.info(f"デフォルトBGMとして '{candidate}' を使用します。")
            return candidate
    
    # どのBGMも見つからなかった場合
    error_message = "BGMファイルが見つかりません。'input/bgm/default_bgm.mp3' または 'sample.mp4' を配置するか、--bgm_path で指定してください。"
    logger.error(error_message)
    raise FileNotFoundError(error_message)