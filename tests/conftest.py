import pytest
import os
import sys
from pathlib import Path

# Add the project root to the Python path more elegantly
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture(autouse=True)
def mock_env_vars():
    """テスト実行時に常にダミーのAPI Keyを設定"""
    os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-testing"
    os.environ["SERP_API_KEY"] = "dummy-serp-api-key"
    os.environ["OPENAI_MODEL"] = "gpt-3.5-turbo"
    os.environ["OPENAI_SEARCH_MODEL"] = "gpt-3.5-turbo"
    yield 