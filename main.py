import logging

import discord
from discord.ext import commands,tasks
from dotenv import load_dotenv
import redis
import secrets
import os
import aiohttp
import asyncio
from urllib.parse import quote_plus
import json
from typing import Optional

# Load environment variables
load_dotenv()

# Constants
TOKEN_EXPIRY = int(os.getenv('TOKEN_EXPIRY'))  # Token expiry in seconds
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
PROXY_URL = os.getenv('PROXY_URL')
CKB_TARGET_URL = os.getenv('CKB_TARGET_URL')
BTC_TARGET_URL = os.getenv('BTC_TARGET_URL')
VERIFIED_ROLE_ID = int(os.getenv('VERIFIED_ROLE_ID'))
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL'))  # Check interval in second
REDIRECT_URI = os.getenv('REDIRECT_URI')
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_KEY_PREFIX = os.getenv('REDIS_KEY_PREFIX')
CKB_ROLE_ID = int(os.getenv('CKB_ROLE_ID'))
BTC_ROLE_ID = int(os.getenv('BTC_ROLE_ID'))
TARGET_GUILD_ID = int(os.getenv('TARGET_GUILD_ID'))
TARGET_CHANNEL_ID = int(os.getenv('TARGET_CHANNEL_ID'))

# Redis connection
redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0)


class OauthButton(discord.ui.View):
    def __init__(self, token):
        super().__init__()
        # We need to quote the query string to make a valid url. Discord will raise an error if it isn't valid.
        url = REDIRECT_URI + "&state=" + quote_plus(token)

        # Link buttons cannot be made with the
        # decorator, so we have to manually create one.
        # We add the quoted url to the button, and add the button to the view.
        self.add_item(discord.ui.Button(label="Click Here", url=url))

        # Initializing the view and adding the button can actually be done in a one-liner at the start if preferred:
        # super().__init__(discord.ui.Button(label="Click Here", url=url))


async def update_message(message: discord.Interaction, content: str, view: discord.ui.View = None):
    await message.edit_original_response(content=content, view=view)


class VerifyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify Your Nervape Holder Role", style=discord.ButtonStyle.grey)
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id.real
        token = secrets.token_urlsafe(16)

        print(f"User {user_id} requested verification with token {token}")

        # Store token with expiry
        redis_client.setex(f"{REDIS_KEY_PREFIX}:discord:user:{user_id}:token", TOKEN_EXPIRY, token)
        redis_client.set(f"{REDIS_KEY_PREFIX}:discord:user:{user_id}", "pending")

        # Send message and store message ID
        await interaction.response.send_message(
            f"Your verification code is: `{token}`\nThis code will expire in {TOKEN_EXPIRY} seconds.",
            view=OauthButton(token),
            ephemeral=True
        )

        # Store message ID for later editing
        message = await interaction.original_response()
        await self.verification_timeout_trigger(interaction, user_id, TOKEN_EXPIRY)

    @staticmethod
    async def verification_timeout_trigger(interaction: discord.Interaction, user_id, timeout):
        await asyncio.sleep(timeout)
        status = redis_client.get(f"{REDIS_KEY_PREFIX}:discord:user:{user_id}")
        if status and status.decode('utf-8') != "verified":
            redis_client.delete(f"{REDIS_KEY_PREFIX}:discord:user:{user_id}")
            await update_message(interaction, "Verification unsuccessful. Please double check your information and restart the verification process again.", VerifyButton())
            return
        else:
            redis_client.set(f"{REDIS_KEY_PREFIX}:discord:user:{user_id}:verified", 1)
        ckb_address = redis_client.get(f"{REDIS_KEY_PREFIX}:discord:user:{user_id}:address:ckb")
        btc_address = redis_client.get(f"{REDIS_KEY_PREFIX}:discord:user:{user_id}:address:btc")
        if btc_address is None:
            await update_message(interaction, "Verification failed, please retry", VerifyButton())
        else:
            await update_message(interaction,
                                 f"Verification successful! This is to confirm that your CKB address is `{ckb_address.decode('utf-8')}` "
                                 f"and your BTC address is `{btc_address.decode('utf-8')}`.\n------\nIf the above is incorrect, please double check your information and restart the verification process immediately.")


class VerificationBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        intents.message_content = True
        intents.guilds = True  # Required for role management
        intents.reactions = True  # Required for button interactions

        self.proxy = PROXY_URL if PROXY_URL else None
        super().__init__(command_prefix="!", intents=intents, proxy=self.proxy)

        # Create session for API calls
        self.session = None


    async def setup_hook(self):
        await self.tree.sync()
        print("Bot is setting up...")
        self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session:
            await self.session.close()
        await super().close()

    async def edit_verification_message(self, user_id: int, content: str):
        """Helper function to edit verification messages"""
        message_id = redis_client.get(f"message:{user_id}")
        if message_id:
            message_id = int(message_id.decode('utf-8'))
            try:
                channel = await self.fetch_user(user_id)
                message = await channel.fetch_message(message_id)
                await message.edit(content=content)
            except discord.NotFound:
                pass

    @tasks.loop(count=1)
    async def send_initial_message(self):
        channel = self.get_channel(TARGET_CHANNEL_ID)
        embed = discord.Embed(title="Thanks for being a Nervape Holder!", description="We use this verification bot to safely verify that you are a Nervape Holder and can receive the CKB Nervape Holder Role in Discord. To get started, click the button below.\n\nBy verifying, you are agreeing to the Terms of Use and Privacy Policy of this verification process.")
        embed.set_footer(text="Made by Nervape Studio with ❤️")
        embed.set_author(name="Nervape Studio", icon_url="https://www.nervape.com/assets/logo_nervape-3f492c1f.svg")
        await channel.send(embed=embed, view=VerifyButton(), silent=True)

    @tasks.loop(seconds=CHECK_INTERVAL)
    async def check_ckb_addresses(self):
        """Check verified addresses against API"""
        while not self.is_closed():
            try:
                # 1. get from redis
                verified_users = redis_client.keys(f"{REDIS_KEY_PREFIX}:discord:user:*:verified")
                print(f"Checking {len(verified_users)} verified users...")
                for user_key in verified_users:
                    if not await self.verify_btc_user(user_key):  # False is the Flag for skip iteration
                        continue

                    await self.verify_ckb_user(user_key)  # False is the Flag for skip iteration

                # 2. get from role members
                guild = self.get_guild(TARGET_GUILD_ID)
                role = guild.get_role(VERIFIED_ROLE_ID)
                if role:
                    members = role.members
                    print(f"Checking {len(members)} role members...")
                    for member in members:
                        if member.id.real in verified_users:  # skip if already checked
                            continue
                        user_key = f"{REDIS_KEY_PREFIX}:discord:user:{member.id}"
                        if not await self.verify_btc_user(user_key):
                            continue
                        if not await self.verify_ckb_user(user_key):
                            continue

            except Exception as e:
                print(f"Error in address check: {e}")
            await asyncio.sleep(CHECK_INTERVAL)

    async def verify_ckb_user(self, user_key):
        return await self.verify_user(user_key, CKB_TARGET_URL, CKB_ROLE_ID, term="ckb")

    async def verify_btc_user(self, user_key):
        return await self.verify_user(user_key, BTC_TARGET_URL, BTC_ROLE_ID, term="btc")

    async def verify_user(self, user_key, target_url, role_id, term="ckb"):
        # remove prefix and decode
        user_key = user_key.decode('utf-8')[len(REDIS_KEY_PREFIX) + 1:]
        user_id = user_key.split(':')[2]
        user_address_key = f"{REDIS_KEY_PREFIX}:discord:user:{user_id}:address:{term}"
        address = redis_client.get(user_address_key)

        if address is None:
            print(f"user {user_id} does not have a valid {term} address!!!")
            # take over user's role if have
            guild = self.get_guild(TARGET_GUILD_ID)
            member = await guild.fetch_member(int(user_id))
            role = guild.get_role(role_id)
            if role and role in member.roles:
                print(f"User {user_id} is no longer a holder, removing role")
                await member.remove_roles(role)
            return False
        address = address.decode("utf-8")

        # Query API
        async with self.session.get(f"{target_url}/{address}") as response:
            print(f"Checking address {address} for user {user_id}")
            if response.status == 200:
                data = await response.json()
                is_holder = data.get('isHolder', False)

                # Give role to user
                guild = self.get_guild(TARGET_GUILD_ID)
                member = await guild.fetch_member(int(user_id))
                role = guild.get_role(role_id)
                if not role:
                    return False
                if is_holder and role not in member.roles:
                    print(f"User {user_id} is a new verified holder, adding role")
                    await member.add_roles(role)
                elif not is_holder and role in member.roles:
                    print(f"User {user_id} is no longer a holder, removing role")
                    await member.remove_roles(role)
        return True

    async def set_verified(self, user_id: int, address: str):
        """Helper function to set user as verified"""
        print(f"User {user_id} verified with address {address}")
        redis_client.delete(f"{REDIS_KEY_PREFIX}:discord:user:{user_id}")
        redis_client.delete(f"{REDIS_KEY_PREFIX}:verify:{user_id}")
        redis_client.set(f"{REDIS_KEY_PREFIX}:user:verified:{user_id}", address)
        await self.edit_verification_message(user_id, "Verification successful!")


def run_bot():
    bot = VerificationBot()

    @bot.event
    async def on_ready():
        print(f"Logged in as {bot.user} (ID: {bot.user.id})")
        if PROXY_URL:
            print(f"Using proxy: {PROXY_URL}")
        print("------")
        bot.check_ckb_addresses.start()
        bot.send_initial_message.start()

    @bot.tree.command(name="verify", description="Start the verification process")
    async def verify_command(interaction: discord.Interaction):
        await interaction.response.send_message(
            "Click the button below to start verification:",
            view=VerifyButton(),
            ephemeral=True
        )

    bot.run(BOT_TOKEN)


if __name__ == "__main__":
    run_bot()
