import pytest
import discord
from unittest.mock import AsyncMock, MagicMock
from src.config import Config

@pytest.fixture
async def mock_redis():
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=b"test_address")
    redis.setex = AsyncMock()
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    redis.keys = AsyncMock(return_value=[b"test_key"])
    return redis

@pytest.fixture
def mock_bot():
    bot = AsyncMock()
    bot.session = AsyncMock()
    bot.session.get = AsyncMock()
    return bot

@pytest.fixture
def mock_discord_interaction():
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.response = AsyncMock()
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
