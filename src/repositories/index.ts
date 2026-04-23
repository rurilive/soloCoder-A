import type { User, Session, MediaFile, MediaType } from '../types';

export class UserRepository {
  private db: D1Database;

  constructor(db: D1Database) {
    this.db = db;
  }

  async findById(id: number): Promise<User | null> {
    const result = await this.db.prepare('SELECT * FROM users WHERE id = ?').bind(id).first<User>();
    return result || null;
  }

  async findByUuid(uuid: string): Promise<User | null> {
    const result = await this.db.prepare('SELECT * FROM users WHERE uuid = ?').bind(uuid).first<User>();
    return result || null;
  }

  async findByUsername(username: string): Promise<User | null> {
    const result = await this.db.prepare('SELECT * FROM users WHERE username = ?').bind(username).first<User>();
    return result || null;
  }

  async findByEmail(email: string): Promise<User | null> {
    const result = await this.db.prepare('SELECT * FROM users WHERE email = ?').bind(email).first<User>();
    return result || null;
  }

  async findByTelegramId(telegramUserId: number): Promise<User | null> {
    const result = await this.db.prepare('SELECT * FROM users WHERE telegram_user_id = ?').bind(telegramUserId).first<User>();
    return result || null;
  }

  async create(user: Omit<User, 'id' | 'created_at' | 'updated_at'>): Promise<User> {
    const now = new Date().toISOString();
    const result = await this.db.prepare(`
      INSERT INTO users (uuid, username, email, password_hash, secret_token, is_active, is_admin, telegram_user_id, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      RETURNING *
    `).bind(
      user.uuid,
      user.username,
      user.email,
      user.password_hash,
      user.secret_token,
      user.is_active ? 1 : 0,
      user.is_admin ? 1 : 0,
      user.telegram_user_id || null,
      now,
      now
    ).first<User>();
    
    if (!result) throw new Error('Failed to create user');
    return result;
  }

  async update(id: number, updates: Partial<Omit<User, 'id'>>): Promise<User | null> {
    const fields: string[] = [];
    const values: unknown[] = [];
    
    const now = new Date().toISOString();
    fields.push('updated_at = ?');
    values.push(now);
    
    if (updates.username !== undefined) {
      fields.push('username = ?');
      values.push(updates.username);
    }
    if (updates.email !== undefined) {
      fields.push('email = ?');
      values.push(updates.email);
    }
    if (updates.password_hash !== undefined) {
      fields.push('password_hash = ?');
      values.push(updates.password_hash);
    }
    if (updates.secret_token !== undefined) {
      fields.push('secret_token = ?');
      values.push(updates.secret_token);
    }
    if (updates.is_active !== undefined) {
      fields.push('is_active = ?');
      values.push(updates.is_active ? 1 : 0);
    }
    if (updates.is_admin !== undefined) {
      fields.push('is_admin = ?');
      values.push(updates.is_admin ? 1 : 0);
    }
    if (updates.telegram_user_id !== undefined) {
      fields.push('telegram_user_id = ?');
      values.push(updates.telegram_user_id);
    }
    
    values.push(id);
    
    const result = await this.db.prepare(`
      UPDATE users SET ${fields.join(', ')} WHERE id = ? RETURNING *
    `).bind(...values).first<User>();
    
    return result || null;
  }

  async list(limit: number = 100, offset: number = 0): Promise<User[]> {
    const result = await this.db.prepare(`
      SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?
    `).bind(limit, offset).all<User>();
    return result.results;
  }

  async count(): Promise<number> {
    const result = await this.db.prepare('SELECT COUNT(*) as count FROM users').first<{ count: number }>();
    return result?.count || 0;
  }
}

export class SessionRepository {
  private db: D1Database;

  constructor(db: D1Database) {
    this.db = db;
  }

  async findBySessionId(sessionId: string): Promise<Session | null> {
    const now = new Date().toISOString();
    const result = await this.db.prepare(`
      SELECT * FROM sessions WHERE session_id = ? AND expires_at > ?
    `).bind(sessionId, now).first<Session>();
    return result || null;
  }

  async create(session: Omit<Session, 'id' | 'created_at' | 'last_activity'>): Promise<Session> {
    const now = new Date().toISOString();
    const result = await this.db.prepare(`
      INSERT INTO sessions (session_id, user_id, ip_address, user_agent, expires_at, created_at, last_activity)
      VALUES (?, ?, ?, ?, ?, ?, ?)
      RETURNING *
    `).bind(
      session.session_id,
      session.user_id,
      session.ip_address || null,
      session.user_agent || null,
      session.expires_at,
      now,
      now
    ).first<Session>();
    
    if (!result) throw new Error('Failed to create session');
    return result;
  }

  async delete(sessionId: string): Promise<boolean> {
    const result = await this.db.prepare('DELETE FROM sessions WHERE session_id = ?').bind(sessionId).run();
    return result.meta.changes > 0;
  }

  async deleteByUserId(userId: number): Promise<number> {
    const result = await this.db.prepare('DELETE FROM sessions WHERE user_id = ?').bind(userId).run();
    return result.meta.changes;
  }
}

export class MediaFileRepository {
  private db: D1Database;

  constructor(db: D1Database) {
    this.db = db;
  }

  async findById(id: number): Promise<MediaFile | null> {
    const result = await this.db.prepare('SELECT * FROM media_files WHERE id = ?').bind(id).first<MediaFile>();
    return result || null;
  }

  async findByFileId(fileId: string): Promise<MediaFile | null> {
    const result = await this.db.prepare('SELECT * FROM media_files WHERE file_id = ?').bind(fileId).first<MediaFile>();
    return result || null;
  }

  async findByUserId(userId: number, limit: number = 50, offset: number = 0): Promise<MediaFile[]> {
    const result = await this.db.prepare(`
      SELECT * FROM media_files WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?
    `).bind(userId, limit, offset).all<MediaFile>();
    return result.results;
  }

  async create(file: Omit<MediaFile, 'id' | 'created_at' | 'updated_at' | 'view_count' | 'is_expired' | 'is_deleted'>): Promise<MediaFile> {
    const now = new Date().toISOString();
    const result = await this.db.prepare(`
      INSERT INTO media_files (
        file_id, user_id, original_filename, media_type, mime_type, file_size,
        width, height, original_path, standard_path, low_path, icon_path,
        original_size, standard_size, low_size, icon_size, telegram_file_id,
        telegram_message_id, is_public, expires_at, require_token, allowed_referers,
        created_at, view_count, is_expired, is_deleted
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0)
      RETURNING *
    `).bind(
      file.file_id,
      file.user_id,
      file.original_filename,
      file.media_type,
      file.mime_type,
      file.file_size,
      file.width || null,
      file.height || null,
      file.original_path,
      file.standard_path || null,
      file.low_path || null,
      file.icon_path || null,
      file.original_size,
      file.standard_size || null,
      file.low_size || null,
      file.icon_size || null,
      file.telegram_file_id || null,
      file.telegram_message_id || null,
      file.is_public ? 1 : 0,
      file.expires_at || null,
      file.require_token ? 1 : 0,
      file.allowed_referers || null,
      now
    ).first<MediaFile>();
    
    if (!result) throw new Error('Failed to create media file');
    return result;
  }

  async update(id: number, updates: Partial<Omit<MediaFile, 'id'>>): Promise<MediaFile | null> {
    const fields: string[] = [];
    const values: unknown[] = [];
    
    const now = new Date().toISOString();
    fields.push('updated_at = ?');
    values.push(now);
    
    const fieldMappings: Record<string, keyof MediaFile> = {
      original_filename: 'original_filename',
      expires_at: 'expires_at',
      is_expired: 'is_expired',
      is_deleted: 'is_deleted',
      deleted_at: 'deleted_at',
      deleted_reason: 'deleted_reason',
      require_token: 'require_token',
      allowed_referers: 'allowed_referers',
      telegram_file_id: 'telegram_file_id',
      telegram_message_id: 'telegram_message_id',
    };
    
    for (const [dbField, modelField] of Object.entries(fieldMappings)) {
      if (modelField in updates) {
        const value = (updates as Record<string, unknown>)[modelField];
        if (typeof value === 'boolean') {
          fields.push(`${dbField} = ?`);
          values.push(value ? 1 : 0);
        } else {
          fields.push(`${dbField} = ?`);
          values.push(value ?? null);
        }
      }
    }
    
    values.push(id);
    
    const result = await this.db.prepare(`
      UPDATE media_files SET ${fields.join(', ')} WHERE id = ? RETURNING *
    `).bind(...values).first<MediaFile>();
    
    return result || null;
  }

  async incrementViewCount(id: number): Promise<void> {
    await this.db.prepare('UPDATE media_files SET view_count = view_count + 1 WHERE id = ?').bind(id).run();
  }

  async list(limit: number = 100, offset: number = 0): Promise<MediaFile[]> {
    const result = await this.db.prepare(`
      SELECT * FROM media_files ORDER BY created_at DESC LIMIT ? OFFSET ?
    `).bind(limit, offset).all<MediaFile>();
    return result.results;
  }

  async count(): Promise<number> {
    const result = await this.db.prepare('SELECT COUNT(*) as count FROM media_files').first<{ count: number }>();
    return result?.count || 0;
  }

  async countByUserId(userId: number): Promise<number> {
    const result = await this.db.prepare('SELECT COUNT(*) as count FROM media_files WHERE user_id = ?').bind(userId).first<{ count: number }>();
    return result?.count || 0;
  }

  async countExpired(): Promise<number> {
    const result = await this.db.prepare(`
      SELECT COUNT(*) as count FROM media_files WHERE is_expired = 1 AND is_deleted = 0
    `).first<{ count: number }>();
    return result?.count || 0;
  }

  async countDeleted(): Promise<number> {
    const result = await this.db.prepare(`
      SELECT COUNT(*) as count FROM media_files WHERE is_deleted = 1
    `).first<{ count: number }>();
    return result?.count || 0;
  }

  async softDeleteExpired(): Promise<number> {
    const now = new Date().toISOString();
    const result = await this.db.prepare(`
      UPDATE media_files 
      SET is_deleted = 1, deleted_at = ?, deleted_reason = 'Auto cleanup: expired file'
      WHERE is_expired = 1 AND is_deleted = 0
    `).bind(now).run();
    return result.meta.changes;
  }

  async hardDeleteOldDeleted(days: number): Promise<number> {
    const cutoffDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString();
    const result = await this.db.prepare(`
      DELETE FROM media_files WHERE is_deleted = 1 AND deleted_at <= ?
    `).bind(cutoffDate).run();
    return result.meta.changes;
  }
}
