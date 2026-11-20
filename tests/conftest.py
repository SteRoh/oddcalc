import pytest

from config import AppConfig


@pytest.fixture
def app_config() -> AppConfig:
    return AppConfig()
