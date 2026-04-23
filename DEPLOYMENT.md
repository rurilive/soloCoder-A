# 图床服务 - Cloudflare Workers 版本

基于 Cloudflare Workers + D1 + R2 构建的高性能图床服务，支持网页端和 Telegram Bot 两种使用方式。

## 功能特性

- 🌐 **网页端** - 完整的 Web 界面，支持上传、管理、分享
- 🤖 **Telegram Bot** - 通过 Bot 上传和管理文件，自动创建用户
- 📦 **多存储支持** - R2 对象存储 + Telegram 频道存储
- 🔐 **访问控制** - 令牌验证、引用者白名单
- ⏰ **过期管理** - 支持设置文件过期时间
- 🗑️ **软删除恢复** - 防止误删重要文件
- 📊 **管理后台** - 用户管理、文件管理、系统清理

## 技术栈

| 服务 | 技术 |
|------|------|
| 运行时 | Cloudflare Workers |
| 数据库 | Cloudflare D1 (SQLite) |
| 文件存储 | Cloudflare R2 + Telegram |
| 框架 | Hono |
| 认证 | JWT + Session |

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
npm install

# 登录 Cloudflare
npx wrangler login
```

### 2. 创建资源

```bash
# 创建 D1 数据库
npx wrangler d1 create imgbed-db

# 创建 R2 存储桶
npx wrangler r2 bucket create imgbed-media
```

### 3. 更新配置

编辑 `wrangler.toml`，替换以下值：

```toml
[[d1_databases]]
binding = "DB"
database_name = "imgbed-db"
database_id = "你的数据库ID"  # 从上面的输出获取

[[r2_buckets]]
binding = "MEDIA_BUCKET"
bucket_name = "imgbed-media"
```

### 4. 设置环境变量

在 Cloudflare Dashboard 中为 Worker 设置以下环境变量：

| 变量名 | 说明 | 示例 |
|--------|------|------|
| SECRET_KEY | JWT 签名密钥 | 随机强密码 |
| JWT_ALGORITHM | JWT 算法 | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 令牌过期时间 | 1440 |
| MAX_FILE_SIZE | 最大文件大小（字节） | 104857600 |
| ALLOWED_IMAGE_TYPES | 允许的图片类型 | image/jpeg,image/png,image/gif,image/webp |
| ALLOWED_VIDEO_TYPES | 允许的视频类型 | video/mp4,video/webm,video/quicktime |
| TELEGRAM_BOT_TOKEN | Telegram Bot Token | 123456:ABC-DEF |
| TELEGRAM_CHANNEL_ID | 存储频道 ID（可选） | -1001234567890 |
| TELEGRAM_WEBHOOK_SECRET | Webhook 密钥 | 随机字符串 |
| ENVIRONMENT | 运行环境 | production |

### 5. 初始化数据库

```bash
# 执行迁移
npx wrangler d1 migrations apply imgbed-db --local
npx wrangler d1 migrations apply imgbed-db --remote
```

### 6. 本地开发

```bash
# 启动开发服务器
npm run dev
```

访问 http://localhost:8787

### 7. 部署

```bash
# 部署到生产环境
npm run deploy
```

## Telegram Bot 配置

### 1. 创建 Bot

1. 访问 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot` 并按提示操作
3. 获取 Bot Token

### 2. 设置 Webhook

部署后访问：
```
https://你的域名/api/telegram/set-webhook
```

### 3. （可选）创建存储频道

1. 创建一个私密频道
2. 将 Bot 添加为频道管理员
3. 获取频道 ID（可以使用 [@username_to_id_bot](https://t.me/username_to_id_bot)）

### 4. Bot 命令

| 命令 | 说明 |
|------|------|
| `/start` | 开始使用，自动创建账号 |
| `/help` | 显示帮助信息 |
| `/token` | 查看访问令牌 |
| `/files` | 查看最近上传的文件 |
| `/stats` | 查看统计信息 |

**上传方式：** 直接发送图片、视频或文档即可上传。

## Mock 数据

项目包含 Mock 数据生成器，可用于开发测试。

### 默认测试账号

| 用户名 | 邮箱 | 密码 | 角色 |
|--------|------|------|------|
| admin | admin@imgbed.local | admin123 | 管理员 |
| demo_user | demo@imgbed.local | demo123 | 普通用户 |
| test_user_01 | test01@imgbed.local | test123 | 普通用户 |

## API 文档

### 认证接口

#### 注册
```
POST /register
Content-Type: application/x-www-form-urlencoded

username=xxx&email=xxx&password=xxx&confirm_password=xxx
```

#### 登录
```
POST /login
Content-Type: application/x-www-form-urlencoded

username=xxx&password=xxx
```

#### 登出
```
POST /logout
```

#### 获取当前用户
```
GET /api/me
Authorization: Bearer <token>
```

### 媒体接口

#### 上传文件
```
POST /upload
Content-Type: multipart/form-data
Authorization: Bearer <token>

file=<文件>
expire_days=0
require_token=false
allowed_referers=
```

#### 访问文件
```
GET /file/{file_id}/{quality}?st=<token>
```

quality 可选值：original, standard, low, icon

#### 更新过期时间
```
PUT /api/media/{file_id}/expire
Content-Type: application/x-www-form-urlencoded

expire_days=7
```

#### 软删除文件
```
POST /api/media/{file_id}/soft-delete
Content-Type: application/x-www-form-urlencoded

reason=xxx
```

#### 恢复文件
```
POST /api/media/{file_id}/restore
```

#### 获取/重置用户令牌
```
GET /api/user/token
POST /api/user/token/reset
```

### 管理接口

需要管理员权限。

#### 切换用户状态
```
POST /api/admin/users/{user_id}/toggle-active
POST /api/admin/users/{user_id}/toggle-admin
```

#### 硬删除文件
```
POST /api/admin/media/{file_id}/hard-delete
```

#### 系统清理
```
POST /api/admin/cleanup/expired      # 软删除过期文件
POST /api/admin/cleanup/permanent    # 永久删除已软删除文件
```

## 项目结构

```
imgbed-worker/
├── src/
│   ├── index.ts              # 主入口
│   ├── types/
│   │   └── index.ts          # 类型定义
│   ├── middleware/
│   │   └── auth.ts           # 认证中间件
│   ├── repositories/
│   │   └── index.ts          # 数据库操作
│   ├── routes/
│   │   ├── auth.ts           # 认证路由
│   │   ├── media.ts          # 媒体路由
│   │   └── admin.ts          # 管理路由
│   └── utils/
│       ├── security.ts       # 安全工具
│       ├── telegram.ts       # Telegram 服务
│       └── mock-data.ts      # Mock 数据
├── migrations/
│   └── 0001_initial_schema.sql
├── wrangler.toml
├── package.json
└── tsconfig.json
```

## 注意事项

### 生产环境

1. **修改 SECRET_KEY** - 使用强随机字符串
2. **启用 HTTPS** - Cloudflare 默认提供
3. **限制 CORS** - 根据需要修改 CORS 配置
4. **设置 Webhook 密钥** - 防止恶意请求

### Telegram Bot

1. Bot 必须是频道管理员才能发送消息到频道
2. 频道 ID 以 `-100` 开头
3. 上传的文件会同时存储在 R2 和 Telegram（如果配置了频道）

### 限制

| 限制项 | 值 |
|--------|-----|
| Worker 单请求内存 | 128MB |
| Worker 单请求执行时间 | 30秒 |
| R2 单文件大小 | 5TB |
| D1 数据库大小 | 1GB（免费版）|
| Telegram Bot 文件上传 | 50MB（通过 Bot API）|

## License

MIT License
