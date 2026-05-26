from pathlib import Path


def test_project_has_expected_backend_package():
    assert Path("talash").is_dir()
    assert Path("talash/main.py").is_file()
