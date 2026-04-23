import type { Context, Next } from 'hono';
import { getCookie } from 'hono/cookie';
import type { Env, User } from '../types';
import { UserRepository, SessionRepository } from '../repositories';
import { verifyAccessToken } from '../utils/security';

export async function authMiddleware(c: Context<{ Bindings: Env }>, next: Next) {
  const user = await getCurrentUser(c);
  c.set('user', user);
  await next();
}

export async function getCurrentUser(c: Context<{ Bindings: Env }>): Promise<User | null> {
  const env = c.env;
  const db = env.DB;
  
  const sessionId = getCookie(c, 'session_id');
  const userRepo = new UserRepository(db);
  const sessionRepo = new SessionRepository(db);
  
  if (sessionId) {
    const session = await sessionRepo.findBySessionId(sessionId);
    if (session) {
      const user = await userRepo.findById(session.user_id);
      if (user && user.is_active === 1) {
        return user;
      }
    }
  }
  
  const accessToken = getCookie(c, 'access_token');
  if (accessToken) {
    const payload = await verifyAccessToken(accessToken, env.SECRET_KEY);
    if (payload && payload.sub) {
      const user = await userRepo.findByUsername(payload.sub);
      if (user && user.is_active === 1) {
        return user;
      }
    }
  }
  
  const authHeader = c.req.header('Authorization');
  if (authHeader && authHeader.startsWith('Bearer ')) {
    const token = authHeader.substring(7);
    const payload = await verifyAccessToken(token, env.SECRET_KEY);
    if (payload && payload.sub) {
      const user = await userRepo.findByUsername(payload.sub);
      if (user && user.is_active === 1) {
        return user;
      }
    }
  }
  
  return null;
}

export async function requireAuth(c: Context<{ Bindings: Env }>, next: Next) {
  const user = c.get('user') as User | null;
  if (!user) {
    return c.json({ error: 'Not authenticated' }, 401);
  }
  await next();
}

export async function requireAdmin(c: Context<{ Bindings: Env }>, next: Next) {
  const user = c.get('user') as User | null;
  if (!user) {
    return c.json({ error: 'Not authenticated' }, 401);
  }
  if (user.is_admin !== 1) {
    return c.json({ error: 'Admin access required' }, 403);
  }
  await next();
}
