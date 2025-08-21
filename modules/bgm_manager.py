# modules/bgm_manager.py
def select_bgm(bgm_path=None):
    if bgm_path:
        return bgm_path
    # 仮: デフォルトBGM
    return "default_bgm.mp3"