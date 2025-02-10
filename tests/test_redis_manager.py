import pytest
from src.redis_manager import RedisManager

@pytest.mark.asyncio
async def test_store_verification_token(mock_redis):
    manager = RedisManager()
    manager.redis = mock_redis
    
    await manager.store_verification_token(12345, "test_token")
    mock_redis.setex.assert_called_once()
    mock_redis.set.assert_called_once()

@pytest.mark.asyncio
async def test_get_verified_users(mock_redis):
    manager = RedisManager()
    manager.redis = mock_redis
    
    users = await manager.get_verified_users()
    mock_redis.keys.assert_called_once()
    assert isinstance(users, list)

@pytest.mark.asyncio
async def test_get_user_addresses(mock_redis):
    manager = RedisManager()
    manager.redis = mock_redis
    
    addresses = await manager.get_user_addresses(12345)
    assert isinstance(addresses, tuple)
    assert len(addresses) == 2
    mock_redis.get.assert_called()
