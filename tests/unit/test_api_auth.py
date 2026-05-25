from unittest.mock import MagicMock

from oure.api.auth import APIKeyManager


def test_api_key_manager_create_and_validate():
    # Mock Redis pool and Redis instance
    mock_pool = MagicMock()
    mock_redis = MagicMock()

    manager = APIKeyManager(mock_pool)
    manager.redis = mock_redis

    # Mock hset to do nothing
    mock_redis.hset.return_value = None

    # Test create_key
    key = manager.create_key("test_label", 60)
    assert isinstance(key, str)
    mock_redis.hset.assert_called_once()

    # Mock exists to return True for valid key
    mock_redis.exists.return_value = 1
    assert manager.validate_key(key) is True

    # Mock exists to return False for invalid key
    mock_redis.exists.return_value = 0
    assert manager.validate_key("invalid_key") is False


def test_api_key_manager_rate_limit():
    mock_pool = MagicMock()
    mock_redis = MagicMock()

    manager = APIKeyManager(mock_pool)
    manager.redis = mock_redis

    key = "test_key"

    # Test within limit
    mock_redis.incr.return_value = 1
    mock_redis.hget.return_value = b"60"
    assert manager.check_rate_limit(key) is True
    mock_redis.expire.assert_called_once()

    # Test exceeding limit
    mock_redis.incr.return_value = 61
    assert manager.check_rate_limit(key) is False
