from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    # Authentication timeouts and tokens
    TOKEN_EXPIRY = int(os.getenv('TOKEN_EXPIRY'))  # Duration in SECONDS before verification tokens expire
    BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')     # Discord bot authentication token from developer portal
    
    # Network configuration
    PROXY_URL = os.getenv('PROXY_URL')             # Optional HTTP/HTTPS proxy for API requests
    
    # Blockchain API endpoints
    CKB_TARGET_URL = os.getenv('CKB_TARGET_URL')   # API endpoint for CKB holder verification
    BTC_TARGET_URL = os.getenv('BTC_TARGET_URL')  # API endpoint for BTC holder verification
    
    # Discord role configuration
    VERIFIED_ROLE_ID = int(os.getenv('VERIFIED_ROLE_ID'))  # Base role ID for verified users
    CKB_ROLE_ID = int(os.getenv('CKB_ROLE_ID'))           # Role ID for CKB holders
    BTC_ROLE_ID = int(os.getenv('BTC_ROLE_ID'))           # Role ID for BTC holders
    
    # Discord server configuration
    TARGET_GUILD_ID = int(os.getenv('TARGET_GUILD_ID'))        # Discord server (guild) ID
    TARGET_CHANNEL_ID = int(os.getenv('TARGET_CHANNEL_ID'))    # Channel ID for verification messages
    
    # Verification process settings
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL'))  # Time in seconds between holder status checks
    REDIRECT_URI = os.getenv('REDIRECT_URI')           # OAuth2 redirect URI for verification flow
    
    # Redis configuration
    REDIS_HOST = os.getenv('REDIS_HOST', 'redis')              # Redis server hostname/IP
    REDIS_KEY_PREFIX = os.getenv('REDIS_KEY_PREFIX', 'nervape')  # Namespace prefix for Redis keys

    # Message Configuration
    MESSAGE_TITLE = os.getenv('MESSAGE_TITLE', 'Thanks for being a Nervape Holder!')
    MESSAGE_DESCRIPTION = os.getenv(
        'MESSAGE_DESCRIPTION',
        'We use this verification bot to safely verify that you are a Nervape Holder and can receive '
        'the Nervape Holder Role in Discord. To get started, click the button below.\n\n'
        'By verifying, you are agreeing to the Terms of Use and Privacy Policy of this verification process.'
    )
    MESSAGE_FOOTER = os.getenv('MESSAGE_FOOTER', 'Made by Nervape Studio with ❤️')
    MESSAGE_AUTHOR_NAME = os.getenv('MESSAGE_AUTHOR_NAME', 'Nervape Studio')
    MESSAGE_AUTHOR_ICON = os.getenv(
        'MESSAGE_AUTHOR_ICON',
        'https://cdn.discordapp.com/icons/942680148212350996/84da741b575d3ac42a5bea3a67b57614.png'
    )
