import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.views import VerifyButton, OauthButton
from src.config import Config
from src.redis_manager import RedisManager

@pytest.mark.asyncio
async def test_oauth_button_creation():
    test_token = "test_token"
    button = OauthButton(test_token)
    assert len(button.children) == 1
    assert button.children[0].label == "Click Here"
    assert Config.REDIRECT_URI in button.children[0].url

@pytest.mark.asyncio
async def test_verify_button_click(mock_discord_interaction, mock_redis):
    with patch('src.views.RedisManager', autospec=True) as MockRedisManager:
        instance = MockRedisManager.return_value
        instance.redis = mock_redis.redis
        instance.prefix = Config.REDIS_KEY_PREFIX
        instance.store_verification_token = AsyncMock()
        
        button = VerifyButton()
        await button.verify_button.callback(mock_discord_interaction)
        
        mock_discord_interaction.response.send_message.assert_called_once()
        call_args = mock_discord_interaction.response.send_message.call_args
        assert "verification code" in call_args[0][0]
        assert isinstance(call_args[1]["view"], OauthButton)
