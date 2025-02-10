from abc import ABC, abstractmethod
import discord
from .config import Config

class BaseRoleManager(ABC):
    def __init__(self, bot, redis_manager):
        self.bot = bot
        self.redis = redis_manager
        self._cached_role = None  # Add role cache
        
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

    @property
    def cached_role(self):
        return self._cached_role
        
    @cached_role.setter
    def cached_role(self, role):
        self._cached_role = role

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

    async def update_role(self, member):
        """Update user's role based on holder status"""
        if not member or not self.cached_role:
            return False

        try:
            user_id = member.id
            is_holder = await self.verify_holder(user_id)
            has_role = self.cached_role in member.roles

            if is_holder and not has_role:
                await member.add_roles(self.cached_role)
                print(f"Added {self.address_key} role to user {user_id}")
                return True
            elif not is_holder and has_role:
                await member.remove_roles(self.cached_role)
                print(f"Removed {self.address_key} role from user {user_id}")
                return True
            return is_holder
        except Exception as e:
            print(f"Error updating {self.address_key} role for user {member.id}: {e}")
            return False

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
