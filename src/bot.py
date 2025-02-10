import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import logging
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

    async def setup_hook(self):
        await self.tree.sync()
        self.session = aiohttp.ClientSession()
        self.role_managers = [
            NervapeCKBRoleManager(self, self.redis),
            NervapeBTCManager(self, self.redis)
        ]

    @tasks.loop(count=1)
    async def init_roles(self):
        """Initialize and cache roles for each manager"""
        print("Initializing role cache...")
        guild = self.get_guild(Config.TARGET_GUILD_ID)
        if not guild:
            print(f"Could not find guild with ID {Config.TARGET_GUILD_ID}")
            return

        for manager in self.role_managers:
            role = guild.get_role(manager.role_id)
            if role:
                manager.cached_role = role
                print(f"Cached role {role.name} for {manager.address_key} manager")
            else:
                print(f"Could not find role with ID {manager.role_id} for {manager.address_key} manager")

    async def get_guild_member(self, user_id: int):
        """Safe method to get guild member"""
        guild = self.get_guild(Config.TARGET_GUILD_ID)
        if guild is None:
            print(f"Could not find guild with ID {Config.TARGET_GUILD_ID}")
        try:
            return await guild.fetch_member(user_id)
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
                print(f"Initial message {last_initial_message} not found")
                pass
        self.redis.redis.set(f"{Config.REDIS_KEY_PREFIX}:discord:last_initial_message", res.id)

    async def verify_role_holder(self, user, manager) -> bool:
        """Verify holder status for a specific chain"""
        try:
            return await manager.update_role(user)
        except Exception as e:
            print(f"Error verifying {manager.address_key} for user {user}: {e}")
            return False

    async def verify_all_roles(self, guild, user) -> bool:
        """Verify holder status for all chains in order"""
        try:
            for manager in self.role_managers:
                if not manager.cached_role:
                    print(f"No cached role for {manager.address_key} manager")
                    # adding cached role for the manager
                    role = guild.get_role(manager.role_id)
                    if role:
                        manager.cached_role = role
                    else:
                        print(f"Could not find role with ID {manager.role_id} for {manager.address_key} manager")
                        continue
                if not await self.verify_role_holder(user, manager):
                    return False
            return True
        except Exception as e:
            print(f"Error verifying chains for user {user}: {e}")
            return False

    async def process_holder_batch(self, members, guild):
        """Process a batch of members in parallel"""
        tasks = [
            self.verify_all_roles(guild, member)
            for member in members
            if member is not None
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    @tasks.loop(seconds=Config.CHECK_INTERVAL)
    async def check_addresses(self):
        """Check verified addresses against API"""
        try:
            # Get guild once
            guild = self.get_guild(Config.TARGET_GUILD_ID)
            if not guild:
                print("Guild not found, skipping check")
                return

            # Get verified users from Redis in one call
            verified_keys = self.redis.redis.keys(f"{Config.REDIS_KEY_PREFIX}:discord:user:*:verified")
            verified_user_ids = {key.decode('utf-8').split(':')[3] for key in verified_keys}
            print(f"Found {len(verified_user_ids)} verified users")

            # Process verified users in batches
            verified_members = []
            for user_id in verified_user_ids:
                try:
                    member = await guild.fetch_member(int(user_id))
                    if member:
                        verified_members.append(member)
                except discord.NotFound:
                    continue
                except Exception as e:
                    print(f"Error fetching member {user_id}: {e}")
            
            # Process all members in batches
            all_members = verified_members
            BATCH_SIZE = 10
            for i in range(0, len(all_members), BATCH_SIZE):
                batch = all_members[i:i + BATCH_SIZE]
                await self.process_holder_batch(batch, guild)
                
        except Exception as e:
            print(f"Error in address check: {e}")

    async def close(self):
        if self.session:
            await self.session.close()
        await super().close()
