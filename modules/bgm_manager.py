import os

# select_bgm 関数の引数に settings を追加
def select_bgm(bgm_path=None, settings=None):
    """
    BGMファイルを選択する。指定がなければデフォルトのBGMを探す。
    """
    if bgm_path:
        if os.path.exists(bgm_path):
            return bgm_path
        else:
            print(f"警告: 指定されたBGMファイル '{bgm_path}' が見つかりません。デフォルトBGMを探します。")

    # デフォルトBGMの候補 (優先順位順) を settings から取得
    default_bgm_candidates = settings['general']['default_bgm_candidates']

    for candidate in default_bgm_candidates:
        if os.path.exists(candidate):
            print(f"  -> デフォルトBGMとして '{candidate}' を使用します。")
            return candidate
    
    # どのBGMも見つからなかった場合
    error_message = "BGMファイルが見つかりません。'input/bgm/default_bgm.mp3' または 'sample.mp4' を配置するか、--bgm_path で指定してください。"
    print(f"エラー: {error_message}")
    raise FileNotFoundError(error_message)
