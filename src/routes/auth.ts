import { Hono } from 'hono';
import { setCookie, deleteCookie, getCookie } from 'hono/cookie';
import type { Env, User, ApiResponse } from '../types';
import { UserRepository, SessionRepository } from '../repositories';
import { hashPassword, verifyPassword, createAccessToken, generateUUID, generateSecretToken, generateSessionId } from '../utils/security';
import { requireAuth, getCurrentUser } from '../middleware/auth';

const auth = new Hono<{ Bindings: Env }>();

auth.get('/register', async (c) => {
  const user = await getCurrentUser(c);
  if (user) {
    return c.redirect('/dashboard');
  }
  return c.html(await renderRegisterPage(c));
});

auth.post('/register', async (c) => {
  const body = await c.req.parseBody();
  const username = body.username as string;
  const email = body.email as string;
  const password = body.password as string;
  const confirmPassword = body.confirm_password as string;
  
  if (password !== confirmPassword) {
    return c.json({ error: 'Passwords do not match' } as ApiResponse, 400);
  }
  
  if (username.length < 3 || username.length > 50) {
    return c.json({ error: 'Username must be between 3 and 50 characters' } as ApiResponse, 400);
  }
  
  if (password.length < 6) {
    return c.json({ error: 'Password must be at least 6 characters' } as ApiResponse, 400);
  }
  
  const userRepo = new UserRepository(c.env.DB);
  
  const existingUser = await userRepo.findByUsername(username);
  if (existingUser) {
    return c.json({ error: 'Username already registered' } as ApiResponse, 400);
  }
  
  const existingEmail = await userRepo.findByEmail(email);
  if (existingEmail) {
    return c.json({ error: 'Email already registered' } as ApiResponse, 400);
  }
  
  const passwordHash = await hashPassword(password);
  
  const user = await userRepo.create({
    uuid: generateUUID(),
    username,
    email,
    password_hash: passwordHash,
    secret_token: generateSecretToken(),
    is_active: 1,
    is_admin: 0,
  });
  
  const userCount = await userRepo.count();
  if (userCount === 1) {
    await userRepo.update(user.id, { is_admin: 1 });
    user.is_admin = 1;
  }
  
  return c.json({
    id: user.id,
    uuid: user.uuid,
    username: user.username,
    email: user.email,
    is_active: user.is_active === 1,
    is_admin: user.is_admin === 1,
    created_at: user.created_at,
  });
});

auth.get('/login', async (c) => {
  const user = await getCurrentUser(c);
  if (user) {
    return c.redirect('/dashboard');
  }
  return c.html(await renderLoginPage(c));
});

auth.post('/login', async (c) => {
  const body = await c.req.parseBody();
  const username = body.username as string;
  const password = body.password as string;
  
  const userRepo = new UserRepository(c.env.DB);
  const sessionRepo = new SessionRepository(c.env.DB);
  
  const user = await userRepo.findByUsername(username);
  
  if (!user || !(await verifyPassword(password, user.password_hash))) {
    return c.json({ error: 'Incorrect username or password' } as ApiResponse, 401);
  }
  
  if (user.is_active !== 1) {
    return c.json({ error: 'User account is disabled' } as ApiResponse, 403);
  }
  
  const ipAddress = c.req.header('CF-Connecting-IP') || c.req.header('X-Forwarded-For');
  const userAgent = c.req.header('User-Agent');
  
  const expiresMinutes = parseInt(c.env.ACCESS_TOKEN_EXPIRE_MINUTES as unknown as string) || 1440;
  const expiresAt = new Date(Date.now() + expiresMinutes * 60 * 1000);
  
  const sessionId = generateSessionId();
  await sessionRepo.create({
    session_id: sessionId,
    user_id: user.id,
    ip_address: ipAddress,
    user_agent: userAgent,
    expires_at: expiresAt.toISOString(),
  });
  
  const accessToken = await createAccessToken(
    user.username,
    c.env.SECRET_KEY,
    expiresMinutes
  );
  
  const cookieOptions = {
    httpOnly: true,
    secure: c.env.ENVIRONMENT === 'production',
    sameSite: 'Lax' as const,
    expires: expiresAt,
    path: '/',
  };
  
  setCookie(c, 'session_id', sessionId, cookieOptions);
  setCookie(c, 'access_token', accessToken, cookieOptions);
  
  return c.json({
    access_token: accessToken,
    token_type: 'bearer',
  });
});

auth.post('/logout', requireAuth, async (c) => {
  const user = c.get('user') as User;
  const sessionRepo = new SessionRepository(c.env.DB);
  
  const sessionId = getCookie(c, 'session_id');
  if (sessionId) {
    await sessionRepo.delete(sessionId);
  }
  
  deleteCookie(c, 'session_id', { path: '/' });
  deleteCookie(c, 'access_token', { path: '/' });
  
  return c.json({ message: 'Successfully logged out' });
});

auth.get('/logout', async (c) => {
  const user = await getCurrentUser(c);
  if (user) {
    const sessionRepo = new SessionRepository(c.env.DB);
    const sessionId = getCookie(c, 'session_id');
    if (sessionId) {
      await sessionRepo.delete(sessionId);
    }
  }
  
  deleteCookie(c, 'session_id', { path: '/' });
  deleteCookie(c, 'access_token', { path: '/' });
  
  return c.redirect('/login');
});

auth.get('/api/me', requireAuth, async (c) => {
  const user = c.get('user') as User;
  return c.json({
    id: user.id,
    uuid: user.uuid,
    username: user.username,
    email: user.email,
    is_active: user.is_active === 1,
    is_admin: user.is_admin === 1,
    created_at: user.created_at,
  });
});

async function renderRegisterPage(c: Context<{ Bindings: Env }>): Promise<string> {
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>注册 - 图床服务</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center p-4">
  <div class="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
    <div class="text-center mb-8">
      <h1 class="text-3xl font-bold text-gray-800 mb-2">创建账号</h1>
      <p class="text-gray-500">加入我们的图床服务</p>
    </div>
    <form id="registerForm" class="space-y-6">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">用户名</label>
        <input type="text" name="username" required minlength="3" maxlength="50"
          class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all">
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">邮箱</label>
        <input type="email" name="email" required
          class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all">
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">密码</label>
        <input type="password" name="password" required minlength="6"
          class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all">
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">确认密码</label>
        <input type="password" name="confirm_password" required
          class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all">
      </div>
      <button type="submit"
        class="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-blue-700 transition-all transform hover:scale-[1.02]">
        注册
      </button>
    </form>
    <div class="mt-6 text-center">
      <p class="text-gray-500">已有账号？<a href="/login" class="text-purple-600 hover:underline font-medium">立即登录</a></p>
    </div>
  </div>
  <script>
    document.getElementById('registerForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(e.target);
      try {
        const res = await fetch('/register', { method: 'POST', body: formData });
        if (res.ok) {
          window.location.href = '/login';
        } else {
          const data = await res.json();
          alert(data.error || '注册失败');
        }
      } catch (err) {
        alert('网络错误');
      }
    });
  </script>
</body>
</html>`;
}

async function renderLoginPage(c: Context<{ Bindings: Env }>): Promise<string> {
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>登录 - 图床服务</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center p-4">
  <div class="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
    <div class="text-center mb-8">
      <h1 class="text-3xl font-bold text-gray-800 mb-2">欢迎回来</h1>
      <p class="text-gray-500">登录您的账号</p>
    </div>
    <form id="loginForm" class="space-y-6">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">用户名</label>
        <input type="text" name="username" required
          class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all">
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">密码</label>
        <input type="password" name="password" required
          class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all">
      </div>
      <button type="submit"
        class="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-blue-700 transition-all transform hover:scale-[1.02]">
        登录
      </button>
    </form>
    <div class="mt-6 text-center">
      <p class="text-gray-500">还没有账号？<a href="/register" class="text-purple-600 hover:underline font-medium">立即注册</a></p>
    </div>
  </div>
  <script>
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(e.target);
      try {
        const res = await fetch('/login', { method: 'POST', body: formData });
        if (res.ok) {
          window.location.href = '/dashboard';
        } else {
          const data = await res.json();
          alert(data.error || '登录失败');
        }
      } catch (err) {
        alert('网络错误');
      }
    });
  </script>
</body>
</html>`;
}

import type { Context } from 'hono';

export { auth };
