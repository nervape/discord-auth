import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import logging
from .config import Config
from .views import VerifyButton
from .redis_manager import RedisManager
from .role_managers import NervapeCKBRoleManager, NervapeBTCManager

# Get Discord's logger
logger = logging.getLogger('discord.client')

class VerificationBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        intents.guilds = True
        intents.members = True  # Make sure this is enabled
        intents.reactions = True
        super().__init__(command_prefix="!", intents=intents, proxy=Config.PROXY_URL)
        self.session = None
        self.redis = RedisManager()
        self.role_managers = []

    async def setup_hook(self):
        await self.tree.sync()
        self.session = aiohttp.ClientSession()
        self.role_managers = [
            NervapeCKBRoleManager(self, self.redis),
            NervapeBTCManager(self, self.redis)
        ]

    async def get_guild_member(self, user_id: int):
        """Safe method to get guild member"""
        guild = self.get_guild(Config.TARGET_GUILD_ID)
        if guild is None:
            logger.error(f"Could not find guild with ID {Config.TARGET_GUILD_ID}")
        try:
            return await guild.fetch_member(user_id)
        except discord.NotFound:
            logger.warning(f"Member {user_id} not found in guild")
            return None
        except Exception as e:
            logger.error(f"Error fetching member {user_id}: {e}")
            return None

    @tasks.loop(count=1)
    async def send_initial_message(self):
        channel = self.get_channel(Config.TARGET_CHANNEL_ID)
        embed = discord.Embed(
            title=Config.MESSAGE_TITLE,
            description=Config.MESSAGE_DESCRIPTION
        )
        embed.set_footer(text=Config.MESSAGE_FOOTER)
        embed.set_author(
            name=Config.MESSAGE_AUTHOR_NAME,
            icon_url=Config.MESSAGE_AUTHOR_ICON
        )
        res = await channel.send(embed=embed, view=VerifyButton(), silent=True)
        
        # Handle previous message cleanup
        last_initial_message = self.redis.redis.get(f"{Config.REDIS_KEY_PREFIX}:discord:last_initial_message")
        if last_initial_message:
            last_initial_message = int(last_initial_message)
            try:
                message = await channel.fetch_message(last_initial_message)
                await message.delete()
            except discord.NotFound:
                logger.info(f"Initial message {last_initial_message} not found")
                pass
        self.redis.redis.set(f"{Config.REDIS_KEY_PREFIX}:discord:last_initial_message", res.id)

    async def verify_role_holder(self, guild, user, manager) -> bool:
        """Verify holder status for a specific chain"""
        try:
            return await manager.update_role(guild, user)
        except Exception as e:
            logger.error(f"Error verifying {manager.address_key} for user {user}: {e}")
            return False

    async def verify_all_roles(self, guild, user) -> bool:
        """Verify holder status for all chains in order"""
        try:
            for manager in self.role_managers:
                if not await self.verify_role_holder(guild, user, manager):
                    return False
            return True
        except Exception as e:
            logger.error(f"Error verifying chains for user {user}: {e}")
            return False

    @tasks.loop(seconds=Config.CHECK_INTERVAL)
    async def check_addresses(self):
        """Check verified addresses against API"""
        while not self.is_closed():
            try:
                # 1. Get verified users from Redis directly
                verified_users = self.redis.redis.keys(f"{Config.REDIS_KEY_PREFIX}:discord:user:*:verified")
                logger.info(f"Checking {len(verified_users)} verified users...")
                
                # Extract user IDs from Redis keys
                verified_user_ids = set(
                    key.decode('utf-8').split(':')[3]  # Get ID part from {prefix}:discord:user:{id}:verified
                    for key in verified_users
                )
                

                guild = self.get_guild(Config.TARGET_GUILD_ID)
                if not guild:
                    logger.error("Guild not found, skipping role member check")
                    continue
                
                # Process each verified user
                for user_key in verified_users:
                    logger.info(f"Processing user {user_key}")
                    try:
                        user_id = user_key.decode('utf-8').split(':')[3]
                        member = await self.get_guild_member(user_id)
                        await self.verify_all_roles(guild ,member)
                    except Exception as e:
                        logger.error(f"Error processing user {user_key}: {e}")
                        continue

                # 2. Check role members
                    
                role = guild.get_role(Config.VERIFIED_ROLE_ID)
                if role:
                    members = role.members
                    logger.info(f"Checking {len(members)} role members...")
                    for member in members:
                        try:
                            # Skip if already checked in verified users using extracted IDs
                            logger.info(f"Checking role member {member.id}")
                            if str(member.id) in verified_user_ids:
                                continue
                                
                            user_key = f"{Config.REDIS_KEY_PREFIX}:discord:user:{member.id}".encode()
                            await self.verify_all_roles(guild, member)
                        except Exception as e:
                            logger.error(f"Error checking role member {member}: {e}")
                            continue

            except Exception as e:
                logger.error(f"Error in address check: {e}")

    async def close(self):
        if self.session:
            await self.session.close()
        await super().close()
