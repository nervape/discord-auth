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
        intents.message_content = True
        intents.messages = True
        intents.guilds = True
        intents.members = True  # Make sure this is enabled
        intents.reactions = True
        super().__init__(command_prefix="!", intents=intents, proxy=Config.PROXY_URL)
        self.session = None
        self.redis = RedisManager()
        self.role_managers = []
        self.guild = None  # Store guild reference
        self._ready = asyncio.Event()  # Add ready event

    async def setup_hook(self):
        await self.tree.sync()
        self.session = aiohttp.ClientSession()
        self.role_managers = [
            NervapeCKBRoleManager(self, self.redis),
            NervapeBTCManager(self, self.redis)
        ]

    async def on_ready(self):
        self.guild = self.get_guild(Config.TARGET_GUILD_ID)
        if not self.guild:
            print(f"Could not find guild with ID {Config.TARGET_GUILD_ID}")
            return
        
        print(f"Connected to guild: {self.guild.name}")
        self._ready.set()  # Signal that bot is ready
        
        # Start background tasks after we're ready
        self.check_addresses.start()
        self.send_initial_message.start()

    async def get_guild_member(self, user_id: int):
        """Safe method to get guild member"""
        if not self.guild:
            print(f"guild is None, please check your configuration")
            return None
        try:
            return await self.guild.fetch_member(user_id)
        except discord.NotFound:
            print(f"Member {user_id} not found in guild")
            return None
        except Exception as e:
            print(f"Error fetching member {user_id}: {e}")
            return None

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
        await self._ready.wait()  # Wait until bot is ready
        
        try:
            verified_users = await self.redis.get_verified_users()
            print(f"Checking {len(verified_users)} verified users...")
            
            for user_id in verified_users:
                member = await self.get_guild_member(int(user_id))
                if not member:
                    continue
                    
                for manager in self.role_managers:
                    try:
                        await manager.update_role(user_id)
                    except Exception as e:
                        print(f"Error checking {manager.address_key} role for user {user_id}: {e}")

        except Exception as e:
            print(f"Error in address check: {e}")

    async def close(self):
        if self.session:
            await self.session.close()
        await super().close()
