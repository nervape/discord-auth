import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
from .config import Config
from .views import VerifyButton
from .redis_manager import RedisManager
from .role_managers import NervapeCKBRoleManager, NervapeBTCManager

class VerificationBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = intents.messages = intents.guilds = intents.members = intents.reactions = True
        super().__init__(command_prefix="!", intents=intents, proxy=Config.PROXY_URL)
        self.session = None
        self.redis = RedisManager()
        self.role_managers = []

    async def setup_hook(self):
        await self.tree.sync()
        self.session = aiohttp.ClientSession()
        # Initialize role managers with new class names
        self.role_managers = [
            NervapeCKBRoleManager(self, self.redis),
            NervapeBTCManager(self, self.redis)
        ]
        self.check_addresses.start()
        self.send_initial_message.start()

    @tasks.loop(count=1)
    async def send_initial_message(self):
        channel = self.get_channel(Config.TARGET_CHANNEL_ID)
        embed = discord.Embed(
            title="Thanks for being a Nervape Holder!",
            description="Click the button below to verify your holder status."
        )
        await channel.send(embed=embed, view=VerifyButton())

    @tasks.loop(seconds=Config.CHECK_INTERVAL)
    async def check_addresses(self):
        while not self.is_closed():
            try:
                # Check verified users from Redis
                verified_users = await self.redis.get_verified_users()
                print(f"Checking {len(verified_users)} verified users...")
                
                # Check each user with all role managers
                for user_id in verified_users:
                    for manager in self.role_managers:
                        try:
                            await manager.update_role(user_id)
                        except Exception as e:
                            print(f"Error checking {manager.address_key} role for user {user_id}: {e}")

                # Check role members
                guild = self.get_guild(Config.TARGET_GUILD_ID)
                role = guild.get_role(Config.VERIFIED_ROLE_ID)
                if role:
                    members = role.members
                    print(f"Checking {len(members)} role members...")
                    for member in members:
                        if str(member.id) in verified_users:
                            continue
                        for manager in self.role_managers:
                            try:
                                await manager.update_role(member.id)
                            except Exception as e:
                                print(f"Error checking {manager.address_key} role for member {member.id}: {e}")

            except Exception as e:
                print(f"Error in address check: {e}")
            await asyncio.sleep(Config.CHECK_INTERVAL)

    async def close(self):
        if self.session:
            await self.session.close()
        await super().close()
