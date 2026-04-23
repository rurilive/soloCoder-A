import * as bcrypt from 'bcryptjs';
import { v4 as uuidv4 } from 'uuid';
import jwt from '@tsndr/cloudflare-worker-jwt';
import type { JwtPayload, QualityLevel } from '../types';

const SALT_ROUNDS = 10;

export async function hashPassword(password: string): Promise<string> {
  const salt = await bcrypt.genSalt(SALT_ROUNDS);
  return bcrypt.hash(password, salt);
}

export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

export function generateUUID(): string {
  return uuidv4();
}

export function generateSessionId(): string {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
}

export function generateFileId(): string {
  const bytes = new Uint8Array(9);
  crypto.getRandomValues(bytes);
  return btoa(String.fromCharCode(...bytes))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

export function generateSecretToken(): string {
  const bytes = new Uint8Array(48);
  crypto.getRandomValues(bytes);
  return btoa(String.fromCharCode(...bytes))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

export async function createAccessToken(
  username: string,
  secretKey: string,
  expiresInMinutes: number
): Promise<string> {
  const now = Math.floor(Date.now() / 1000);
  const payload: JwtPayload = {
    sub: username,
    iat: now,
    exp: now + expiresInMinutes * 60,
  };
  
  return jwt.sign(payload, secretKey, {
    algorithm: 'HS256',
  });
}

export async function verifyAccessToken(
  token: string,
  secretKey: string
): Promise<JwtPayload | null> {
  try {
    const isValid = await jwt.verify(token, secretKey, {
      algorithm: 'HS256',
    });
    
    if (!isValid) return null;
    
    const decoded = jwt.decode(token) as { payload: JwtPayload };
    return decoded.payload;
  } catch {
    return null;
  }
}

export function hashFilename(filename: string): string {
  const timestamp = Date.now().toString();
  const randomBytes = new Uint8Array(16);
  crypto.getRandomValues(randomBytes);
  const randomStr = Array.from(randomBytes, (b) => b.toString(16).padStart(2, '0')).join('');
  
  const hashInput = `${filename}${timestamp}${randomStr}`;
  const encoder = new TextEncoder();
  const data = encoder.encode(hashInput);
  
  return Array.from(new Uint8Array(data.slice(0, 32)), (b) => b.toString(16).padStart(2, '0')).join('');
}

export const QUALITY_CONFIGS: Record<QualityLevel, { maxWidth: number; maxHeight: number; quality: number; suffix: string }> = {
  original: { maxWidth: 0, maxHeight: 0, quality: 100, suffix: 'original' },
  standard: { maxWidth: 1920, maxHeight: 1080, quality: 85, suffix: 'standard' },
  low: { maxWidth: 800, maxHeight: 600, quality: 60, suffix: 'low' },
  icon: { maxWidth: 200, maxHeight: 200, quality: 70, suffix: 'icon' },
};

export function parseAllowedTypes(typesStr: string): string[] {
  return typesStr.split(',').map((t) => t.trim());
}

export function getFileExtension(filename: string): string {
  const ext = filename.split('.').pop();
  return ext ? ext.toLowerCase() : '';
}
