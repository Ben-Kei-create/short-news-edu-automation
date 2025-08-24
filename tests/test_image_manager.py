import pytest
from unittest.mock import patch, MagicMock
import google.generativeai as genai  # Added missing import
import requests  # Added missing import
from modules.image_manager import _generate_image_prompts, generate_images, load_manual_images


@pytest.fixture
def mock_settings():
    return {
        'api_keys': {
            'gemini': 'mock_gemini_api_key'
        },
        'general': {
            'placeholder_image_path': 'mock_placeholder.png',
            'num_images_needed': 12
        },
        'stable_diffusion': {
            'api_url': 'http://localhost:7860/sdapi/v1/txt2img',
            'steps': 20,
            'width': 512,
            'height': 768,
            'negative_prompt': 'bad quality',
            'quality_keywords': 'masterpiece, best quality'
        }
    }


def test_load_manual_images_empty_folder():
    """空のフォルダを指定した場合をテスト"""
    images = load_manual_images("nonexistent_folder")
    assert images == []


def test_load_manual_images_none_folder():
    """Noneを指定した場合をテスト"""
    images = load_manual_images(None)
    assert images == []


@patch('os.path.exists')
@patch('glob.glob')
def test_load_manual_images_with_files(mock_glob, mock_exists):
    """画像ファイルが存在する場合をテスト"""
    mock_exists.return_value = True
    mock_glob.return_value = ['image1.png', 'image2.jpg', 'image1.png']  # 重複あり
    
    images = load_manual_images("test_folder")
    assert len(images) == 2  # 重複除去後
    assert 'image1.png' in images
    assert 'image2.jpg' in images


@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
def test_generate_image_prompts_success(mock_configure, mock_GenerativeModel, mock_settings):
    """Gemini APIで画像プロンプト生成が成功した場合をテスト"""
    mock_model_instance = MagicMock()
    mock_GenerativeModel.return_value = mock_model_instance
    mock_model_instance.generate_content.return_value.text = "prompt1\nprompt2\nprompt3"
    
    prompts = _generate_image_prompts("テーマ", "スタイル", 3, mock_settings)
    
    assert len(prompts) == 3
    assert prompts == ["prompt1", "prompt2", "prompt3"]
    mock_configure.assert_called_once_with(api_key='mock_gemini_api_key')


@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
def test_generate_image_prompts_api_error(mock_configure, mock_GenerativeModel, mock_settings):
    """Gemini APIエラーが発生した場合をテスト"""
    mock_model_instance = MagicMock()
    mock_GenerativeModel.return_value = mock_model_instance
    # Use Exception instead of non-existent types.APIError
    mock_model_instance.generate_content.side_effect = Exception("API Error")
    
    prompts = _generate_image_prompts("テーマ", "スタイル", 2, mock_settings)
    
    assert prompts == []


@patch('modules.image_manager._generate_image_prompts')
@patch('os.makedirs')
@patch('builtins.open', new_callable=MagicMock)
@patch('modules.image_manager.datetime')
@patch('base64.b64decode')
@patch('requests.post')
def test_generate_images_sd_api_success(mock_requests_post, mock_b64decode, mock_datetime, mock_open, mock_makedirs, mock_generate_image_prompts, mock_settings):
    """Stable Diffusion APIで画像生成が成功した場合をテスト"""
    mock_datetime.now.return_value.strftime.return_value = "20230101_120000"
    mock_generate_image_prompts.return_value = ["prompt1", "prompt2"]
    
    # Mock base64 decode to return fake image data
    mock_b64decode.return_value = b"fake_image_data"
    
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {'images': ["iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77zgAAAABJRU5ErkJggg=="]}
    mock_requests_post.return_value = mock_response
    
    images = generate_images("テーマ", "スタイル", num=2, use_sd_api=True, settings=mock_settings)
    
    assert len(images) == 2
    assert all('input/images/20230101_120000' in img_path for img_path in images)


@patch('modules.image_manager._generate_image_prompts')
@patch('os.makedirs')
@patch('builtins.open', new_callable=MagicMock)
@patch('modules.image_manager.datetime')
@patch('requests.post')
def test_generate_images_sd_api_fallback(mock_requests_post, mock_datetime, mock_open, mock_makedirs, mock_generate_image_prompts, mock_settings):
    """Stable Diffusion APIエラーでプレースホルダーにフォールバックする場合をテスト"""
    mock_datetime.now.return_value.strftime.return_value = "20230101_120000"
    mock_generate_image_prompts.return_value = ["prompt1"]
    mock_requests_post.side_effect = requests.exceptions.RequestException("API error")
    
    images = generate_images("テーマ", "スタイル", num=1, use_sd_api=True, settings=mock_settings)
    
    assert len(images) == 1
    assert images[0] == 'mock_placeholder.png'


def test_generate_images_no_sd_api(mock_settings):
    """Stable Diffusion APIを使わない場合をテスト"""
    with patch('os.path.exists', return_value=True):
        images = generate_images("テーマ", "スタイル", num=3, use_sd_api=False, settings=mock_settings)
        
        assert len(images) == 3
        assert all(img == 'mock_placeholder.png' for img in images)


def test_generate_images_zero_num(mock_settings):
    """num=0を指定した場合をテスト"""
    images = generate_images("テーマ", "スタイル", num=0, settings=mock_settings)
    assert images == []
