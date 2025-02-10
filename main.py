import logging
from src.bot import VerificationBot
from src.views import VerifyButton
from src.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    bot = VerificationBot()
    
    @bot.event
    async def on_ready():
        logger.info(f"Bot logged in as {bot.user}")
        bot.send_initial_message.start()
        bot.check_addresses.start()
        bot.init_roles.start()

    @bot.tree.command(name="verify", description="Start the verification process")
    async def verify_command(interaction):
        await interaction.response.send_message(
            "Click the button below to start verification:",
            view=VerifyButton(),
            ephemeral=True
        )

    try:
        bot.run(Config.BOT_TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    main()
