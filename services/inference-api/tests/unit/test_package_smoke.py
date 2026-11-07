# services/inference-api/tests/unit/test_package_smoke.py
# Xac nhan goi visign_api duoc cai va import duoc trong moi truong CP1.
import importlib


def test_visign_api_package_is_importable() -> None:
    # Given moi truong da dong bo dependency; When import goi; Then dung ten module
    inference_package = importlib.import_module("visign_api")

    assert inference_package.__name__ == "visign_api"
