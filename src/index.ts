import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { prettyJSON } from 'hono/pretty-json';
import type { Env, TelegramUpdate, MediaFile } from './types';
import { authMiddleware } from './middleware/auth';
import { auth } from './routes/auth';
import { media } from './routes/media';
import { admin } from './routes/admin';
import { TelegramBotHandler, TelegramService } from './utils/telegram';
import { MediaFileRepository, UserRepository } from './repositories';

const app = new Hono<{ Bindings: Env }>();

app.use('*', prettyJSON());
app.use('*', cors({
  origin: '*',
  allowHeaders: ['Content-Type', 'Authorization'],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE'],
}));
app.use('*', authMiddleware);

app.get('/', async (c) => {
  const user = c.get('user');
  if (user) {
    return c.redirect('/dashboard');
  }
  
  return c.html(`<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>图床服务 - 高性能图片托管</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-cyan-50">
  <nav class="bg-white/80 backdrop-blur-sm shadow-sm sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16 items-center">
        <span class="text-2xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">ImgBed</span>
        <div class="flex gap-4">
          <a href="/login" class="px-4 py-2 text-gray-600 hover:text-purple-600 transition-colors">登录</a>
          <a href="/register" class="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all">注册</a>
        </div>
      </div>
    </div>
  </nav>
  
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
    <div class="text-center mb-16">
      <h1 class="text-5xl md:text-6xl font-bold text-gray-800 mb-6">
        高性能<span class="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">图床服务</span>
      </h1>
      <p class="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
        支持多质量图片转换、分享链接管理、访问控制，同时提供网页端和 Telegram Bot 两种使用方式
      </p>
      <div class="flex flex-wrap justify-center gap-4">
        <a href="/register" class="px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white text-lg font-semibold rounded-xl hover:from-purple-700 hover:to-blue-700 transition-all transform hover:scale-105 shadow-lg">
          立即开始
        </a>
        <a href="#features" class="px-8 py-4 bg-white text-gray-700 text-lg font-semibold rounded-xl hover:bg-gray-50 transition-all shadow-lg border border-gray-200">
          了解更多
        </a>
      </div>
    </div>
    
    <div id="features" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-20">
      <div class="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-shadow">
        <div class="w-14 h-14 bg-gradient-to-br from-purple-100 to-purple-200 rounded-xl flex items-center justify-center mb-6">
          <svg class="w-7 h-7 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
          </svg>
        </div>
        <h3 class="text-xl font-bold text-gray-800 mb-3">多质量转换</h3>
        <p class="text-gray-600">支持原图、标准、低清、图标四种质量等级，自动生成不同尺寸的图片版本</p>
      </div>
      
      <div class="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-shadow">
        <div class="w-14 h-14 bg-gradient-to-br from-blue-100 to-blue-200 rounded-xl flex items-center justify-center mb-6">
          <svg class="w-7 h-7 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
          </svg>
        </div>
        <h3 class="text-xl font-bold text-gray-800 mb-3">访问控制</h3>
        <p class="text-gray-600">支持令牌验证和引用者白名单，灵活控制文件访问权限</p>
      </div>
      
      <div class="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-shadow">
        <div class="w-14 h-14 bg-gradient-to-br from-green-100 to-green-200 rounded-xl flex items-center justify-center mb-6">
          <svg class="w-7 h-7 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
          </svg>
        </div>
        <h3 class="text-xl font-bold text-gray-800 mb-3">Telegram Bot</h3>
        <p class="text-gray-600">通过 Telegram Bot 上传和管理文件，随时随地分享图片和视频</p>
      </div>
      
      <div class="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-shadow">
        <div class="w-14 h-14 bg-gradient-to-br from-yellow-100 to-yellow-200 rounded-xl flex items-center justify-center mb-6">
          <svg class="w-7 h-7 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
        </div>
        <h3 class="text-xl font-bold text-gray-800 mb-3">过期管理</h3>
        <p class="text-gray-600">支持设置文件过期时间，自动清理临时文件</p>
      </div>
      
      <div class="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-shadow">
        <div class="w-14 h-14 bg-gradient-to-br from-red-100 to-red-200 rounded-xl flex items-center justify-center mb-6">
          <svg class="w-7 h-7 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
          </svg>
        </div>
        <h3 class="text-xl font-bold text-gray-800 mb-3">软删除恢复</h3>
        <p class="text-gray-600">支持软删除和恢复功能，防止误删重要文件</p>
      </div>
      
      <div class="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-shadow">
        <div class="w-14 h-14 bg-gradient-to-br from-cyan-100 to-cyan-200 rounded-xl flex items-center justify-center mb-6">
          <svg class="w-7 h-7 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"></path>
          </svg>
        </div>
        <h3 class="text-xl font-bold text-gray-800 mb-3">Cloudflare 原生</h3>
        <p class="text-gray-600">基于 Workers、D1、R2 构建，全球 CDN 加速，极致性能</p>
      </div>
    </div>
    
    <div class="text-center py-12">
      <p class="text-gray-500">
        准备好开始了吗？<a href="/register" class="text-purple-600 hover:underline font-medium">立即注册</a> 或 <a href="/login" class="text-purple-600 hover:underline font-medium">登录</a>
      </p>
    </div>
  </div>
</body>
</html>`);
});

app.route('/', auth);
app.route('/', media);
app.route('/', admin);

app.post('/api/telegram/webhook', async (c) => {
  const secretToken = c.req.header('X-Telegram-Bot-Api-Secret-Token');
  
  if (secretToken !== c.env.TELEGRAM_WEBHOOK_SECRET) {
    return c.json({ error: 'Unauthorized' }, 401);
  }
  
  try {
    const update = await c.req.json<TelegramUpdate>();
    const handler = new TelegramBotHandler(c.env);
    await handler.handleUpdate(update);
    return c.json({ ok: true });
  } catch (error) {
    console.error('Telegram webhook error:', error);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

app.get('/api/telegram/set-webhook', async (c) => {
  const url = new URL(c.req.url);
  const webhookUrl = `${url.origin}/api/telegram/webhook`;
  
  const service = new TelegramService(c.env);
  const result = await service.setWebhook(webhookUrl, c.env.TELEGRAM_WEBHOOK_SECRET);
  
  return c.json(result);
});

app.get('/api/telegram/delete-webhook', async (c) => {
  const service = new TelegramService(c.env);
  const result = await service.deleteWebhook();
  return c.json(result);
});

app.get('/file/telegram/:telegramFileId/:quality', async (c) => {
  const telegramFileId = c.req.param('telegramFileId');
  const quality = c.req.param('quality');
  const st = c.req.query('st');

  const service = new TelegramService(c.env);
  
  try {
    const fileUrl = await service.getFileUrl(telegramFileId);
    
    const response = await fetch(fileUrl);
    if (!response.ok) {
      return c.json({ error: 'File not found' }, 404);
    }
    
    const blob = await response.blob();
    return new Response(blob, {
      headers: {
        'Content-Type': blob.type || 'application/octet-stream',
        'Cache-Control': 'public, max-age=31536000',
      },
    });
  } catch (error) {
    console.error('Telegram file fetch error:', error);
    return c.json({ error: 'Failed to fetch file from Telegram' }, 500);
  }
});

app.get('/api/health', (c) => {
  return c.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    worker: 'imgbed-worker',
  });
});

app.onError((err, c) => {
  console.error('Application error:', err);
  return c.json({
    error: 'Internal Server Error',
    message: c.env.ENVIRONMENT === 'production' ? undefined : err.message,
  }, 500);
});

app.notFound((c) => {
  return c.json({ error: 'Not Found' }, 404);
});

export default app;
