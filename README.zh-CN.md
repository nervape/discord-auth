# Discord Auth bot

自动化的Discord Holder验证和权限组管理。基于Redis。

## 前置

- Python 3.8+
- Redis 6.0+
- Discord 机器人令牌和应用程序
- 一个符合规格的HTTP/HTTPS API（见下文API规范）

## 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/nervape/discord-auth.git
cd discord-auth
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 创建 `.env` 文件：
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

## API 集成规范

验证 API 端点必须实现以下接口：

```typescript
// 响应接口
interface VerificationResponse {
  isHolder: boolean;        // 必需：持有者状态
  tokenCount?: number;      // 可选：持有代币数量
  lastUpdated?: string;     // 可选：时间戳
  error?: string;          // 可选：错误信息
}

// 示例端点：GET /api/verify/{chain}/{address}
// 示例响应：
{
  "isHolder": true,
  "tokenCount": 5,
  "lastUpdated": "2023-11-24T12:00:00Z"
}

// 错误响应：
{
  "isHolder": false,
  "error": "无效的地址格式"
}
```

端点要求：
- 需要实现GET请求
- 需要以JSON响应
- 建议添加响应缓存以降低服务端压力

## 使用说明

### 基础设置

1. 创建 Discord 应用程序和机器人：
   - 访问 Discord 开发者平台
   - 创建新应用程序
   - 进入机器人设置页面
   - 启用以下INTENT：
     - MESSAGE CONTENT INTENT（消息内容意图）
     - SERVER MEMBERS INTENT（服务器成员意图）
     - PRESENCE INTENT（在线状态意图）

2. 邀请机器人至服务器，需要以下权限：
   - 管理角色（用于分配/移除角色）
   - 读取消息/查看频道（用于读取验证请求）
   - 发送消息（用于回复用户）
   - 嵌入链接（用于验证按钮）
   - 读取消息历史（用于跟踪验证状态）
   - 使用外部表情符号（用于UI元素）
   - 添加反应（用于交互元素）
   
   可以使用此权限计算链接：
   `https://discord.com/api/oauth2/authorize?client_id=你的客户端ID&permissions=268435456&scope=bot%20applications.commands`

3. 配置服务器设置：
   - 确保机器人的角色位于它需要管理的角色之上
   - 创建验证频道（保存ID用于配置）
   - 创建不同类型的持有者角色（保存ID用于配置）

4. 运行机器人：
```bash
python main.py
```

5. 验证设置：
   - 机器人应显示在线
   - 验证消息应出现在指定频道
   - 使用样例地址测试验证流程

### 开发指南

#### 项目结构

```
src/
├── bot.py          # 核心机器人实现
├── config.py       # 配置管理
├── redis_manager.py # 状态管理
├── role_managers.py # 角色管理系统
└── views.py        # Discord UI 组件
```

#### 实现自定义角色管理器

1. 在 `role_managers.py` 中创建新的角色管理器：
```python
class SporeRoleManager(BaseRoleManager):
    @property
    def role_id(self) -> int:
        return Config.SPORE_ROLE_ID
        
    @property
    def address_key(self) -> str:
        return 'spore'
        
    @property
    def verification_url(self) -> str:
        return Config.SPORE_TARGET_URL
```

2. 在 `config.py` 中添加配置：
```python
SPORE_ROLE_ID = int(os.getenv('SPORE_ROLE_ID'))
SPORE_TARGET_URL = os.getenv('SPORE_TARGET_URL')
```

3. 在 `bot.py` 中注册新管理器：
```python
self.role_managers = [
    CKBRoleManager(self, self.redis),
    BTCRoleManager(self, self.redis),
    SPORERoleManager(self, self.redis)
]
```

## 部署方案

### 1. Docker 部署（推荐）

```bash
docker compose up -d
```

### 2. 系统服务部署

创建 systemd 服务文件：
```ini
[Unit]
Description=Discord NFT 验证机器人
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

## 许可证

MIT 许可证
