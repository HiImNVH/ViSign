# tests/integration/conftest.py
# Test tich hop o goc repo dung chung bo dung artifact T036 voi test tich hop cua API (T064).
import sys
from pathlib import Path

API_INTEGRATION_TESTS = (
    Path(__file__).resolve().parents[2]
    / "services"
    / "inference-api"
    / "tests"
    / "integration"
)
# Module t036_artifact_builder chi duoc import ben trong test sau khi da kiem extra serving
if str(API_INTEGRATION_TESTS) not in sys.path:
    sys.path.insert(0, str(API_INTEGRATION_TESTS))
