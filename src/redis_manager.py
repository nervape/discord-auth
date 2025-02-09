import redis
from .config import Config

class RedisManager:
    def __init__(self):
        try:
            self.redis = redis.Redis(host=Config.REDIS_HOST, port=6379, db=0)
            self.prefix = Config.REDIS_KEY_PREFIX
        except Exception as e:
            print(f"Redis connection failed: {e}")
            self.redis = None
            self.prefix = Config.REDIS_KEY_PREFIX

    async def store_verification_token(self, user_id: int, token: str):
        try:
            key = f"{self.prefix}:discord:user:{user_id}:token"
            self.redis.setex(key, Config.TOKEN_EXPIRY, token)
            self.redis.set(f"{self.prefix}:discord:user:{user_id}", "pending")
        except Exception as e:
            print(f"Redis operation failed: {e}")

    async def get_verified_users(self):
        try:
            pattern = f"{self.prefix}:discord:user:*:verified"
            keys = self.redis.keys(pattern)
            return [key.decode('utf-8').split(':')[3] for key in keys if len(key.decode('utf-8').split(':')) > 3]
        except Exception as e:
            print(f"Redis operation failed: {e}")
            return []

    async def get_user_addresses(self, user_id: int):
        try:
            ckb_key = f"{self.prefix}:discord:user:{user_id}:address:ckb"
            btc_key = f"{self.prefix}:discord:user:{user_id}:address:btc"
            return (self.redis.get(ckb_key), self.redis.get(btc_key))
        except Exception as e:
            print(f"Redis operation failed: {e}")
            return (None, None)
