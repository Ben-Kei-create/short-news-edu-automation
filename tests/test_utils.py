import os
import pytest
import yaml
from modules.utils import ensure_folder, load_settings

# テスト用の設定ファイルを作成・削除するフィクスチャ
@pytest.fixture
def temp_settings_file(tmp_path):
    settings_content = """
general:
  test_value: 123
"""
    file_path = tmp_path / "test_settings.yaml"
    file_path.write_text(settings_content)
    return file_path

def test_ensure_folder_creates_folder(tmp_path):
    """存在しないフォルダが作成されることをテスト"""
    test_folder = tmp_path / "new_folder"
    ensure_folder(str(test_folder))
    assert test_folder.is_dir()

def test_ensure_folder_does_nothing_if_exists(tmp_path):
    """存在するフォルダに対しては何もしないことをテスト"""
    test_folder = tmp_path / "existing_folder"
    test_folder.mkdir()
    ensure_folder(str(test_folder))
    assert test_folder.is_dir() # エラーが発生しないことを確認

def test_load_settings_loads_correctly(temp_settings_file):
    """設定ファイルが正しく読み込まれることをテスト"""
    settings = load_settings(str(temp_settings_file))
    assert settings is not None
    assert settings["general"]["test_value"] == 123

def test_load_settings_returns_none_if_not_found(tmp_path):
    """設定ファイルが見つからない場合にNoneを返すことをテスト"""
    non_existent_file = tmp_path / "non_existent.yaml"
    settings = load_settings(str(non_existent_file))
    assert settings is None

def test_load_settings_returns_none_if_invalid_yaml(tmp_path):
    """YAML形式が不正な場合にNoneを返すことをテスト"""
    invalid_yaml_content = "general:\n  - item1\n- item2: value" # 不正なYAML
    file_path = tmp_path / "invalid.yaml"
    file_path.write_text(invalid_yaml_content)
    settings = load_settings(str(file_path))
    assert settings is None
