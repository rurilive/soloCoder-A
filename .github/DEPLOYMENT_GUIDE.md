# GitHub CI/CD 部署指南

## 前置准备

### 1. Cloudflare 账户设置

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 获取以下信息：
   - **Account ID**: 在 Workers & Pages 页面右侧
   - **API Token**: 右上角头像 -> My Profile -> API Tokens -> Create Token
     - 选择 `Edit Cloudflare Workers` 模板
     - 或自定义权限：Workers R2 Storage, D1, Workers Scripts

### 2. 创建 Cloudflare 资源

**创建 D1 数据库：**
```bash
npx wrangler d1 create imgbed-db
```
记录返回的 `database_id`。

**创建 R2 存储桶：**
```bash
npx wrangler r2 bucket create imgbed-media
```

### 3. 设置 GitHub Secrets

在 GitHub 仓库中进入 **Settings → Secrets and variables → Actions**，添加以下 Secrets：

| Secret 名称 | 说明 | 示例值 |
|------------|------|--------|
| `CLOUDFLARE_API_TOKEN` | Cloudflare API Token | `abc123def456...` |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare 账户 ID | `a1b2c3d4...` |
| `CLOUDFLARE_D1_DB_ID` | D1 数据库 ID | `12345678-1234...` |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | `123456:ABC-DEF...` |
| `TELEGRAM_CHANNEL_ID` | 备份频道 ID | `-1001234567890` |
| `TELEGRAM_WEBHOOK_SECRET` | Webhook 密钥 | `your-secret-key` |
| `SECRET_KEY` | JWT 签名密钥 | `secure-random-key-32chars+` |

---

## 部署流程

### 自动部署（推荐）

当代码推送到 `main` 或 `master` 分支时，GitHub Actions 会自动：

1. 🧪 运行所有测试
2. 📋 类型检查
3. 🚀 部署到 Cloudflare Workers
4. 🗄️ 执行数据库迁移

### 手动触发

在 GitHub 仓库中：
1. 进入 **Actions** 页面
2. 选择 **Deploy to Cloudflare Workers**
3. 点击 **Run workflow**

### 创建 Release 部署

创建新的 Release 时也会触发自动部署。

---

## 本地开发与测试

### 安装依赖
```bash
npm install
```

### 本地运行
```bash
npm run dev
```

### 运行测试
```bash
npm run test
```

### 本地部署测试
```bash
npm run deploy
```

---

## 环境变量说明

### 必需变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `SECRET_KEY` | JWT 签名密钥（至少32字符） | - |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API Token | - |
| `CLOUDFLARE_D1_DB_ID` | D1 数据库 ID | - |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot 令牌 | - |
| `TELEGRAM_WEBHOOK_SECRET` | Webhook 验证密钥 | - |

### 可选变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `TELEGRAM_CHANNEL_ID` | 私密备份频道 ID | - |
| `JWT_ALGORITHM` | JWT 签名算法 | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间（分钟） | `1440` (24小时) |
| `MAX_FILE_SIZE` | 最大文件大小（字节） | `104857600` (100MB) |
| `ALLOWED_IMAGE_TYPES` | 允许的图片类型 | `image/jpeg,image/png,image/gif,image/webp` |
| `ALLOWED_VIDEO_TYPES` | 允许的视频类型 | `video/mp4,video/webm,video/quicktime` |
| `ENVIRONMENT` | 运行环境 | `production` |

---

## Telegram Bot 设置

### 1. 创建 Bot
1. 与 [@BotFather](https://t.me/BotFather) 对话
2. 发送 `/newbot` 并按提示操作
3. 记录 Bot Token

### 2. 设置 Webhook（部署后）

部署完成后，设置 Telegram Webhook：

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://<YOUR_WORKER_URL>/telegram-webhook",
    "secret_token": "<YOUR_WEBHOOK_SECRET>"
  }'
```

或访问：
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://<YOUR_WORKER_URL>/telegram-webhook&secret_token=<YOUR_WEBHOOK_SECRET>
```

### 3. 验证 Webhook
```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

---

## 数据库迁移

### 首次部署
首次部署时 CI/CD 会自动执行迁移。

### 添加新迁移
在 `migrations/` 目录创建新的 SQL 文件，命名格式：
```
0002_add_new_feature.sql
```

### 手动执行迁移
```bash
# 本地
npx wrangler d1 migrations apply imgbed-db --local

# 生产环境
npx wrangler d1 migrations apply imgbed-db --remote
```

---

## 故障排查

### 部署失败
1. 检查 GitHub Secrets 是否正确配置
2. 查看 Actions 日志获取详细错误
3. 确认 Cloudflare API Token 有足够权限

### 数据库连接问题
1. 确认 D1 数据库 ID 正确
2. 确认 API Token 有 D1 编辑权限
3. 检查迁移文件语法

### Telegram Bot 无响应
1. 确认 Bot Token 正确
2. 确认 Webhook 设置正确
3. 检查 Worker 日志（Cloudflare Dashboard → Workers → imgbed-worker → Logs）

---

## 回滚部署

如需回滚到之前的版本：

1. 在 Cloudflare Dashboard 进入 Workers → imgbed-worker
2. 选择 **Deployments** 标签
3. 找到要回滚的版本，点击 **Rollback**

或使用 CLI：
```bash
# 查看部署历史
npx wrangler deployments list

# 回滚到指定版本
npx wrangler rollback <deployment-id>
```
