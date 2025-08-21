# modules/thumbnail_generator.py
from moviepy.editor import ImageClip
from pathlib import Path

def generate_thumbnail(images, output_file="output/thumbnails/thumbnail.png"):
    """
    画像リストからサムネイル生成
    デフォルトは最初の画像を使用
    Args:
        images (list): 画像パスリスト
        output_file (str): 出力サムネイル
    Returns:
        str: 出力ファイルパス
    """
    try:
        if not images:
            print("サムネイル生成: 画像がありません")
            return None

        # 最初の画像をそのままサムネイルに
        thumb = ImageClip(images[0])
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        thumb.save_frame(output_file)
        print(f"サムネイル生成完了: {output_file}")
        return output_file

    except Exception as e:
        print(f"サムネイル生成エラー: {e}")
        return None