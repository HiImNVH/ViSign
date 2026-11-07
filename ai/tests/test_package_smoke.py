# ai/tests/test_package_smoke.py
# Xac nhan goi visign_ai duoc cai va import duoc trong moi truong CP1.
import importlib


def test_visign_ai_package_is_importable() -> None:
    # Given moi truong da dong bo dependency; When import goi; Then dung ten module
    pipeline_package = importlib.import_module("visign_ai")

    assert pipeline_package.__name__ == "visign_ai"
