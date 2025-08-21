# modules/thumbnail_generator.py

from moviepy.video.VideoClip import ImageClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from pathlib import Path

def generate_thumbnail(
    image_path: str,
    title_text: str,
    series_text: str = "しくじりニュース#1",
    output_path: str = "output/thumbnail.jpg",
):
    """
    自動サムネイル生成
    
    Parameters:
        image_path : str : メイン画像のパス
        title_text : str : 動画タイトル用テキスト
        series_text : str : シリーズ名テキスト
        output_path : str : 出力ファイルパス
    """
    # メイン画像を読み込み
    img_clip = ImageClip(image_path).resize(height=1280)  # 縦動画サイズ基準
    img_width, img_height = img_clip.size

    # タイトルテキスト
    title_clip = TextClip(
        txt=title_text,
        fontsize=80,
        color='white',
        font='Arial-Bold',
        stroke_color='black',
        stroke_width=2,
        method='caption',
        size=(img_width - 40, None)
    ).set_position(("center", 50))  # 上部に配置

    # シリーズテキスト
    series_clip = TextClip(
        txt=series_text,
        fontsize=50,
        color='yellow',
        font='Arial-Bold',
        stroke_color='black',
        stroke_width=2
    ).set_position(("center", img_height - 150))  # 下部に配置

    # 合成
    final_clip = CompositeVideoClip([img_clip, title_clip, series_clip])
    
    # 静止画として書き出し
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    final_clip.save_frame(output_path)
    print(f"Thumbnail saved to {output_path}")


# ===== 使用例 =====
if __name__ == "__main__":
    generate_thumbnail(
        image_path="output/example_image.jpg",
        title_text="ノーベル、爆弾で大失敗!?",
        series_text="しくじりニュース#5",
        output_path="output/thumbnail.jpg"
    )
