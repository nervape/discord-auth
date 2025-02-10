# Discord Asset Holder Verification Bot

[简体中文说明](README.zh-CN.md)

A modular Discord bot built with Python for automated NFT holder verification and role management. Implements an extensible architecture for multi-chain support with built-in Redis caching.

## Technical Requirements

- Python 3.8+
- Redis 6.0+
- Discord Bot Token & Application
- HTTP/HTTPS endpoints for blockchain verification

## Installation

1. Clone the repository:
```bash
git clone https://github.com/nervape/discord-auth.git
cd discord-auth
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```env
DISCORD_BOT_TOKEN=your_bot_token
TOKEN_EXPIRY=3600
PROXY_URL=
CKB_TARGET_URL=https://api.example.com/ckb
BTC_TARGET_URL=https://api.example.com/btc
VERIFIED_ROLE_ID=123456789
CHECK_INTERVAL=300
REDIRECT_URI=https://your-auth-endpoint.com/callback
REDIS_HOST=localhost
REDIS_KEY_PREFIX=nervape
CKB_ROLE_ID=123456789
BTC_ROLE_ID=123456789
TARGET_GUILD_ID=123456789
TARGET_CHANNEL_ID=123456789
```

## API Integration Specification

Your verification API endpoints must implement the following interface:

```typescript
// Response interface
interface VerificationResponse {
  isHolder: boolean;        // Required: holder status
  tokenCount?: number;      // Optional: number of tokens held
  lastUpdated?: string;     // Optional: ISO 8601 timestamp
  error?: string;          // Optional: error message if any
}

// Example endpoint: GET /api/verify/{chain}/{address}
// Example response:
{
  "isHolder": true,
  "tokenCount": 5,
  "lastUpdated": "2023-11-24T12:00:00Z"
}

// Error response:
{
  "isHolder": false,
  "error": "Invalid address format"
}
```

Endpoint requirements:
- Must accept GET requests
- Must return JSON responses
- Should cache results (recommended: 5-15 minutes)

## Usage

### Quick Setup Guide

1. Create Discord Application:
   - Visit [Discord Developer Portal](https://discord.com/developers/applications)
   - Create New Application -> Bot -> Copy Token
   - Enable Privileged Intents (Messages, Server Members, Presence)
   
2. Invite Bot:
   ```
   https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=268435456&scope=bot%20applications.commands
   ```

3. Configure Environment:
   - Copy `.env.example` to `.env`
   - Set `DISCORD_BOT_TOKEN` from step 1
   - Set `TARGET_GUILD_ID` (Right click server -> Copy ID)
   - Set `TARGET_CHANNEL_ID` (Right click channel -> Copy ID)
   - Set role IDs (Server Settings -> Roles -> Copy ID)

Resources:
- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Discord Developer Docs](https://discord.com/developers/docs)
- [Bot Permissions Calculator](https://discordapi.com/permissions.html)

For detailed setup instructions, see Basic Setup section below.

### Basic Setup

1. Create a Discord Application and Bot:
   - Go to Discord Developer Portal
   - Create a new application
   - Navigate to the Bot section
   - Enable the following Privileged Gateway Intents:
     - MESSAGE CONTENT INTENT
     - SERVER MEMBERS INTENT
     - PRESENCE INTENT

2. Invite the bot to your server with these permissions:
   - Manage Roles (to assign/remove roles)
   - Read Messages/View Channels (to read verification requests)
   - Send Messages (to respond to users)
   - Embed Links (for verification buttons)
   - Read Message History (to track verification status)
   - Use External Emojis (for UI elements)
   - Add Reactions (for interactive elements)
   
   You can use this permission calculator link: 
   `https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=268435456&scope=bot%20applications.commands`

3. Configure server settings:
   - Ensure the bot's role is ABOVE the roles it needs to manage
   - Create the verification channel (save ID for config)
   - Create roles for different holder types (save IDs for config)

4. Run the bot:
```bash
python main.py
```

5. Verify the setup:
   - Bot should appear online
   - Verification message should appear in the designated channel
   - Test the verification process with a sample address

### Development

### Architecture Overview

```
src/
├── bot.py          # Core bot implementation
├── config.py       # Configuration management
├── redis_manager.py # State management
├── role_managers.py # Role management system
└── views.py        # Discord UI components
```

### Implementing Custom Role Managers

1. Create a new role manager in `role_managers.py`:
```python
class ETHRoleManager(BaseRoleManager):
    @property
    def role_id(self) -> int:
        return Config.ETH_ROLE_ID
        
    @property
    def address_key(self) -> str:
        return 'eth'
        
    @property
    def verification_url(self) -> str:
        return Config.ETH_TARGET_URL
```

2. Add configuration in `config.py`:
```python
ETH_ROLE_ID = int(os.getenv('ETH_ROLE_ID'))
ETH_TARGET_URL = os.getenv('ETH_TARGET_URL')
```

3. Register the new manager in `bot.py`:
```python
self.role_managers = [
    CKBRoleManager(self, self.redis),
    BTCRoleManager(self, self.redis),
    ETHRoleManager(self, self.redis)
]
```

## Deployment

### 1. Docker (Recommended)

```bash
docker compose up -d
```

### 2. System Service

Create a systemd service file:
```ini
[Unit]
Description=Discord NFT Verification Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/path/to/discord-auth
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Testing

Install development dependencies:
```
pip install -r dev-requirements.txt
```

Run tests:
```
pytest
```

## License

MIT License
