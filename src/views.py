import discord
from urllib.parse import quote_plus
import secrets
from .redis_manager import RedisManager
from .config import Config

class OauthButton(discord.ui.View):
    def __init__(self, token):
        super().__init__()
        url = Config.REDIRECT_URI + "&state=" + quote_plus(token)
        self.add_item(discord.ui.Button(label="Click Here", url=url))

class VerifyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify Your Nervape Holder Role", style=discord.ButtonStyle.grey)
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        redis = RedisManager()
        user_id = interaction.user.id.real
        token = secrets.token_urlsafe(16)
        
        await redis.store_verification_token(user_id, token)
        await interaction.response.send_message(
            f"Your verification code is: `{token}`\nThis code will expire in {Config.TOKEN_EXPIRY} seconds.",
            view=OauthButton(token),
            ephemeral=True
        )
