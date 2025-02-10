import pytest
import discord
from unittest.mock import AsyncMock, MagicMock
from src.redis_manager import RedisManager
from src.config import Config

class AsyncContextManager:
    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.fixture
def mock_redis():
    redis = MagicMock()  # Main mock is synchronous
    redis.redis = MagicMock()  # Internal redis client is also synchronous
    redis.redis.get.return_value = b"test_address"
    redis.redis.setex.return_value = True
    redis.redis.set.return_value = True
    redis.redis.delete.return_value = True
    redis.redis.keys.return_value = [b"test:discord:user:12345:verified"]
    redis.prefix = Config.REDIS_KEY_PREFIX
    return redis

@pytest.fixture
def mock_bot():
    bot = MagicMock()
    session = MagicMock()
    
    # Create a mock response that will be returned by the context manager
    response = AsyncMock()
    response.status = 200
    response.json = AsyncMock(return_value={"isHolder": True})
    
    # Set up the session.get to return a proper async context manager
    session.get = MagicMock(return_value=AsyncContextManager(response))
    bot.session = session
    return bot

@pytest.fixture
def mock_button():
    button = MagicMock(spec=discord.ui.Button)
    return button

@pytest.fixture
def mock_discord_interaction():
    interaction = AsyncMock()
    interaction.response = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.user = MagicMock()
    interaction.user.id = 12345
    return interaction

@pytest.fixture
def mock_guild():
    guild = MagicMock(spec=discord.Guild)
    role = MagicMock(spec=discord.Role)
    role.id = Config.VERIFIED_ROLE_ID
    guild.get_role.return_value = role
    return guild

@pytest.fixture
def mock_member():
    member = AsyncMock(spec=discord.Member)
    member.roles = []
    return member
