import pytest
from unittest.mock import AsyncMock, MagicMock
from src.role_managers import NervapeCKBRoleManager, NervapeBTCManager
from src.config import Config
from tests.conftest import AsyncContextManager

@pytest.mark.asyncio
async def test_nervape_ckb_role_manager_properties():
    manager = NervapeCKBRoleManager(None, None)
    assert manager.role_id == Config.CKB_ROLE_ID
    assert manager.address_key == 'ckb'
    assert manager.verification_url == Config.CKB_TARGET_URL

@pytest.mark.asyncio
async def test_nervape_btc_role_manager_properties():
    manager = NervapeBTCManager(None, None)
    assert manager.role_id == Config.BTC_ROLE_ID
    assert manager.address_key == 'btc'
    assert manager.verification_url == Config.BTC_TARGET_URL

@pytest.mark.asyncio
async def test_get_address(mock_bot, mock_redis):
    manager = NervapeCKBRoleManager(mock_bot, mock_redis)
    mock_redis.redis.get.return_value = b"test_address"  # Set synchronous return value
    
    address = await manager.get_address(12345)
    assert address == "test_address"
    mock_redis.redis.get.assert_called_once()

@pytest.mark.asyncio
async def test_verify_holder_success(mock_bot, mock_redis):
    manager = NervapeCKBRoleManager(mock_bot, mock_redis)
    mock_redis.redis.get.return_value = b"test_address"
    
    # Create response for success case
    response = AsyncMock()
    response.status = 200
    response.json = AsyncMock(return_value={"isHolder": True})
    
    # Update the session.get mock directly
    mock_bot.session.get.return_value = AsyncContextManager(response)
    
    result = await manager.verify_holder(12345)
    assert result is True

@pytest.mark.asyncio
async def test_verify_holder_failure(mock_bot, mock_redis):
    manager = NervapeCKBRoleManager(mock_bot, mock_redis)
    mock_redis.redis.get.return_value = b"test_address"
    
    # Create response for failure case
    response = AsyncMock()
    response.status = 200
    response.json = AsyncMock(return_value={"isHolder": False})
    
    # Update the session.get mock directly
    mock_bot.session.get.return_value = AsyncContextManager(response)
    
    result = await manager.verify_holder(12345)
    assert result is False
