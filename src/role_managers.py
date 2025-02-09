from abc import ABC, abstractmethod
import discord
from .config import Config

class BaseRoleManager(ABC):
    def __init__(self, bot, redis_manager):
        self.bot = bot
        self.redis = redis_manager
        
    @property
    @abstractmethod
    def role_id(self) -> int:
        pass
    
    @property
    @abstractmethod
    def address_key(self) -> str:
        """Redis key suffix for the address (e.g., 'ckb' or 'btc')"""
        pass
    
    @property
    @abstractmethod
    def verification_url(self) -> str:
        """URL to verify holder status"""
        pass

    async def get_address(self, user_id: int) -> str:
        """Get user's address from Redis"""
        key = f"{self.redis.prefix}:discord:user:{user_id}:address:{self.address_key}"
        try:
            address = self.redis.redis.get(key)  # Access underlying redis connection
            return address.decode('utf-8') if address else None
        except Exception as e:
            print(f"Redis operation failed: {e}")
            return None

    async def verify_holder(self, user_id: int) -> bool:
        """Verify if user is still a holder"""
        address = await self.get_address(user_id)
        if not address:
            print(f"Could not find {self.address_key} address for user {user_id}")
            return False
            
        async with self.bot.session.get(f"{self.verification_url}/{address}") as response:
            if response.status == 200:
                data = await response.json()
                return data.get('isHolder', False)
        return False

    async def update_role(self, guild, member):
        """Update user's role based on holder status"""
        if not member:
            print(f"Could not find member with ID {member}, skipping...")
            return
        
        user_id = member.id

        role = guild.get_role(self.role_id)
        if not role:
            print(f"Could not find role with ID {self.role_id}")
            return

        is_holder = await self.verify_holder(user_id)
        
        if is_holder and role not in member.roles:
            print(f"User {user_id} is a new verified {self.address_key} holder, adding role")
            await member.add_roles(role)
        elif not is_holder and role in member.roles:
            print(f"User {user_id} is no longer a {self.address_key} holder, removing role")
            await member.remove_roles(role)
        elif is_holder and role in member.roles:
            print(f"User {user_id} is still a verified {self.address_key} holder")

class NervapeCKBRoleManager(BaseRoleManager):
    @property
    def role_id(self) -> int:
        return Config.CKB_ROLE_ID
        
    @property
    def address_key(self) -> str:
        return 'ckb'
        
    @property
    def verification_url(self) -> str:
        return Config.CKB_TARGET_URL

class NervapeBTCManager(BaseRoleManager):
    @property
    def role_id(self) -> int:
        return Config.BTC_ROLE_ID
        
    @property
    def address_key(self) -> str:
        return 'btc'
        
    @property
    def verification_url(self) -> str:
        return Config.BTC_TARGET_URL

__all__ = ['BaseRoleManager', 'NervapeCKBRoleManager', 'NervapeBTCManager']
