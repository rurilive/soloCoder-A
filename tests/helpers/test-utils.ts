import type { Env, User, MediaFile, Session, MediaType } from '../../src/types';
import { generateUUID, generateSecretToken, generateFileId, hashPassword } from '../../src/utils/security';
import { MOCK_USERS, generateMockMediaFiles } from '../../src/utils/mock-data';

export interface TestResult {
  name: string;
  passed: boolean;
  error?: string;
  duration: number;
  category: string;
}

export interface TestReport {
  totalTests: number;
  passedTests: number;
  failedTests: number;
  duration: number;
  startedAt: string;
  completedAt: string;
  results: TestResult[];
  categories: Record<string, { total: number; passed: number; failed: number }>;
}

export interface MockContext {
  env: Env;
  state: Record<string, unknown>;
  cookies: Record<string, string>;
  headers: Record<string, string>;
}

export class MockD1Database {
  private tables: Record<string, Record<number, unknown>> = {};
  private sequences: Record<string, number> = {};

  constructor() {
    this.initTables();
  }

  private initTables(): void {
    this.tables['users'] = {};
    this.tables['sessions'] = {};
    this.tables['media_files'] = {};
    this.sequences['users'] = 0;
    this.sequences['sessions'] = 0;
    this.sequences['media_files'] = 0;
  }

  private nextId(table: string): number {
    this.sequences[table] = (this.sequences[table] || 0) + 1;
    return this.sequences[table];
  }

  prepare(sql: string): MockD1Statement {
    return new MockD1Statement(this, sql);
  }

  async insert(table: string, data: Record<string, unknown>): Promise<number> {
    const id = this.nextId(table);
    const record = { id, ...data } as Record<number, unknown>;
    this.tables[table][id] = record;
    return id;
  }

  async select(table: string, where?: (record: Record<string, unknown>) => boolean): Promise<unknown[]> {
    const records = Object.values(this.tables[table] || {}) as Record<string, unknown>[];
    if (where) {
      return records.filter(where);
    }
    return records;
  }

  async selectOne(table: string, where: (record: Record<string, unknown>) => boolean): Promise<unknown | null> {
    const records = await this.select(table, where);
    return records[0] || null;
  }

  async update(table: string, where: (record: Record<string, unknown>) => boolean, data: Record<string, unknown>): Promise<number> {
    let count = 0;
    for (const [id, record] of Object.entries(this.tables[table] || {})) {
      const typedRecord = record as Record<string, unknown>;
      if (where(typedRecord)) {
        this.tables[table][Number(id)] = { ...typedRecord, ...data };
        count++;
      }
    }
    return count;
  }

  async delete(table: string, where: (record: Record<string, unknown>) => boolean): Promise<number> {
    let count = 0;
    for (const [id, record] of Object.entries(this.tables[table] || {})) {
      const typedRecord = record as Record<string, unknown>;
      if (where(typedRecord)) {
        delete this.tables[table][Number(id)];
        count++;
      }
    }
    return count;
  }

  getTables(): Record<string, Record<number, unknown>> {
    return this.tables;
  }

  async populateMockData(): Promise<{ users: User[]; mediaFiles: MediaFile[] }> {
    const createdUsers: User[] = [];
    const createdFiles: MediaFile[] = [];

    for (const mockUser of MOCK_USERS) {
      const now = new Date().toISOString();
      const passwordHash = await hashPassword(mockUser.password);
      const uuid = generateUUID();
      
      const userId = await this.insert('users', {
        uuid,
        username: mockUser.username,
        email: mockUser.email,
        password_hash: passwordHash,
        secret_token: generateSecretToken(),
        is_active: 1,
        is_admin: mockUser.is_admin ? 1 : 0,
        telegram_user_id: null,
        created_at: now,
        updated_at: now,
      });

      const userRecord = await this.selectOne('users', (r) => r.id === userId) as User;
      createdUsers.push(userRecord);

      const fileCount = mockUser.is_admin ? 15 : Math.floor(Math.random() * 15) + 5;
      const mockFiles = generateMockMediaFiles(fileCount, userId, uuid);

      for (const mf of mockFiles) {
        const fileId = generateFileId();
        const ext = mf.filename.split('.').pop() || 'jpg';
        const uuidParts = uuid.split('-').slice(0, 2).join('/');
        
        const isExpired = !mockUser.is_admin && Math.random() > 0.7;
        const isDeleted = !mockUser.is_admin && Math.random() > 0.9;
        const requiresToken = Math.random() > 0.8;
        
        const createdDate = new Date();
        createdDate.setDate(createdDate.getDate() - Math.floor(Math.random() * 90));
        
        let expiresAt: string | null = null;
        if (isExpired) {
          const expireDate = new Date(createdDate);
          expireDate.setDate(expireDate.getDate() + Math.floor(Math.random() * 30) + 1);
          expiresAt = expireDate.toISOString();
        }

        const fileSize = mf.media_type === 'image'
          ? Math.floor(Math.random() * 9 * 1024 * 1024) + 100 * 1024
          : Math.floor(Math.random() * 49 * 1024 * 1024) + 1 * 1024 * 1024;

        await this.insert('media_files', {
          file_id: fileId,
          user_id: userId,
          original_filename: mf.filename,
          media_type: mf.media_type,
          mime_type: mf.mime_type,
          file_size: fileSize,
          width: mf.width,
          height: mf.height,
          original_path: `${uuidParts}/${fileId}_original.${ext}`,
          standard_path: mf.media_type === 'image' ? `${uuidParts}/${fileId}_standard.${ext}` : null,
          low_path: mf.media_type === 'image' ? `${uuidParts}/${fileId}_low.${ext}` : null,
          icon_path: mf.media_type === 'image' ? `${uuidParts}/${fileId}_icon.${ext}` : null,
          original_size: fileSize,
          standard_size: mf.media_type === 'image' ? Math.floor(fileSize * 0.6) : null,
          low_size: mf.media_type === 'image' ? Math.floor(fileSize * 0.3) : null,
          icon_size: mf.media_type === 'image' ? Math.floor(fileSize * 0.1) : null,
          telegram_file_id: null,
          telegram_message_id: null,
          is_public: 1,
          view_count: mf.view_count || Math.floor(Math.random() * 1000),
          created_at: createdDate.toISOString(),
          updated_at: null,
          expires_at: expiresAt,
          is_expired: isExpired ? 1 : 0,
          is_deleted: isDeleted ? 1 : 0,
          deleted_at: isDeleted ? new Date().toISOString() : null,
          deleted_reason: isDeleted ? 'Test mock data' : null,
          require_token: requiresToken ? 1 : 0,
          allowed_referers: requiresToken && Math.random() > 0.5 ? 'example.com, test.com' : null,
        });

        const fileRecord = await this.selectOne('media_files', (r) => (r as { file_id: string }).file_id === fileId) as MediaFile;
        createdFiles.push(fileRecord);
      }
    }

    return { users: createdUsers, mediaFiles: createdFiles };
  }
}

export class MockD1Statement {
  private db: MockD1Database;
  private sql: string;
  private bindings: unknown[] = [];

  constructor(db: MockD1Database, sql: string) {
    this.db = db;
    this.sql = sql;
  }

  bind(...bindings: unknown[]): MockD1Statement {
    this.bindings = [...this.bindings, ...bindings];
    return this;
  }

  async all<T>(): Promise<{ results: T[] }> {
    const tables = this.db.getTables();
    
    if (this.sql.includes('SELECT') && this.sql.includes('FROM users')) {
      const results = Object.values(tables['users'] || {}) as T[];
      return { results };
    }
    if (this.sql.includes('SELECT') && this.sql.includes('FROM media_files')) {
      const results = Object.values(tables['media_files'] || {}) as T[];
      return { results };
    }
    
    return { results: [] };
  }

  async first<T>(): Promise<T | null> {
    const tables = this.db.getTables();
    
    if (this.sql.includes('SELECT') && this.sql.includes('FROM users')) {
      const users = Object.values(tables['users'] || {}) as T[];
      if (this.bindings.length > 0) {
        const binding = this.bindings[0];
        const filtered = users.filter((u: unknown) => {
          const user = u as Record<string, unknown>;
          return user.username === binding || user.email === binding || user.id === binding;
        });
        return filtered[0] || null;
      }
      return users[0] || null;
    }
    
    if (this.sql.includes('SELECT') && this.sql.includes('FROM media_files')) {
      const files = Object.values(tables['media_files'] || {}) as T[];
      if (this.bindings.length > 0) {
        const binding = this.bindings[0];
        const filtered = files.filter((f: unknown) => {
          const file = f as Record<string, unknown>;
          return file.file_id === binding || file.id === binding || file.user_id === binding;
        });
        return filtered[0] || null;
      }
      return files[0] || null;
    }
    
    return null;
  }

  async run(): Promise<{ success: boolean; meta: { changes: number; last_row_id: number } }> {
    return {
      success: true,
      meta: { changes: 0, last_row_id: 0 },
    };
  }
}

export class MockR2Bucket {
  private objects: Map<string, R2Object> = new Map();

  async put(
    key: string,
    value: ReadableStream | ArrayBuffer | ArrayBufferView | string | null,
    options?: R2PutOptions
  ): Promise<R2Object> {
    const now = new Date();
    const obj: R2Object = {
      key,
      version: '',
      size: typeof value === 'string' ? value.length : (value as ArrayBuffer)?.byteLength || 0,
      etag: '',
      httpEtag: '',
      uploaded: now,
      checksum: undefined,
      customMetadata: options?.customMetadata,
      httpMetadata: options?.httpMetadata as R2HTTPMetadata,
    };
    this.objects.set(key, obj);
    return obj;
  }

  async get(key: string): Promise<R2ObjectBody | null> {
    const obj = this.objects.get(key);
    if (!obj) return null;
    
    return {
      ...obj,
      body: new ReadableStream(),
      bodyUsed: false,
      arrayBuffer: async () => new ArrayBuffer(0),
      text: async () => '',
      json: async () => ({}),
      writeHttpMetadata: (_headers: Headers) => {},
    } as R2ObjectBody;
  }

  async delete(key: string): Promise<void> {
    this.objects.delete(key);
  }

  getObjects(): Map<string, R2Object> {
    return this.objects;
  }
}

export function createMockEnv(): Env {
  return {
    DB: new MockD1Database() as unknown as D1Database,
    MEDIA_BUCKET: new MockR2Bucket() as unknown as R2Bucket,
    SECRET_KEY: 'test-secret-key-12345678901234567890',
    JWT_ALGORITHM: 'HS256',
    ACCESS_TOKEN_EXPIRE_MINUTES: 1440,
    MAX_FILE_SIZE: 104857600,
    ALLOWED_IMAGE_TYPES: 'image/jpeg,image/png,image/gif,image/webp',
    ALLOWED_VIDEO_TYPES: 'video/mp4,video/webm,video/quicktime',
    TELEGRAM_BOT_TOKEN: 'test-telegram-token',
    TELEGRAM_CHANNEL_ID: '-1001234567890',
    TELEGRAM_WEBHOOK_SECRET: 'test-webhook-secret',
    ENVIRONMENT: 'test',
  };
}

export async function runTest(
  name: string,
  category: string,
  testFn: () => Promise<void>
): Promise<TestResult> {
  const startTime = performance.now();
  try {
    await testFn();
    const duration = performance.now() - startTime;
    return { name, category, passed: true, duration };
  } catch (error) {
    const duration = performance.now() - startTime;
    return {
      name,
      category,
      passed: false,
      duration,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

export function assertEqual(actual: unknown, expected: unknown, message?: string): void {
  if (actual !== expected) {
    throw new Error(message || `Assertion failed: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  }
}

export function assertTrue(value: boolean, message?: string): void {
  if (!value) {
    throw new Error(message || 'Assertion failed: expected true');
  }
}

export function assertFalse(value: boolean, message?: string): void {
  if (value) {
    throw new Error(message || 'Assertion failed: expected false');
  }
}

export function assertNotNull(value: unknown, message?: string): void {
  if (value === null || value === undefined) {
    throw new Error(message || 'Assertion failed: expected not null/undefined');
  }
}

export function assertThrows(fn: () => void, message?: string): void {
  try {
    fn();
    throw new Error(message || 'Assertion failed: expected function to throw');
  } catch {
    // Expected
  }
}
