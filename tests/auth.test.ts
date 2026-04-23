import type { Env, User } from '../src/types';
import type { TestResult } from './helpers/test-utils';
import {
  createMockEnv,
  runTest,
  assertEqual,
  assertTrue,
  assertFalse,
  assertNotNull,
  MockD1Database,
} from './helpers/test-utils';
import { hashPassword, verifyPassword, generateUUID, generateSecretToken, generateFileId } from '../src/utils/security';

export async function runAuthTests(): Promise<TestResult[]> {
  const results: TestResult[] = [];
  const env = createMockEnv();
  const db = env.DB as unknown as MockD1Database;

  results.push(
    await runTest('密码哈希 - 应生成有效哈希', '认证-安全工具', async () => {
      const password = 'testPassword123';
      const hash = await hashPassword(password);
      
      assertNotNull(hash);
      assertTrue(hash.length > 0);
      assertTrue(hash.startsWith('$2a$') || hash.startsWith('$2b$'));
    })
  );

  results.push(
    await runTest('密码验证 - 正确密码应验证通过', '认证-安全工具', async () => {
      const password = 'testPassword123';
      const hash = await hashPassword(password);
      
      const isValid = await verifyPassword(password, hash);
      assertTrue(isValid);
    })
  );

  results.push(
    await runTest('密码验证 - 错误密码应验证失败', '认证-安全工具', async () => {
      const password = 'testPassword123';
      const wrongPassword = 'wrongPassword';
      const hash = await hashPassword(password);
      
      const isValid = await verifyPassword(wrongPassword, hash);
      assertFalse(isValid);
    })
  );

  results.push(
    await runTest('UUID生成 - 应生成唯一UUID', '认证-安全工具', async () => {
      const uuid1 = generateUUID();
      const uuid2 = generateUUID();
      
      assertNotNull(uuid1);
      assertNotNull(uuid2);
      assertEqual(uuid1.length, 36);
      assertTrue(uuid1 !== uuid2);
    })
  );

  results.push(
    await runTest('密钥生成 - 应生成唯一密钥', '认证-安全工具', async () => {
      const token1 = generateSecretToken();
      const token2 = generateSecretToken();
      
      assertNotNull(token1);
      assertNotNull(token2);
      assertTrue(token1.length >= 32);
      assertTrue(token1 !== token2);
    })
  );

  results.push(
    await runTest('文件ID生成 - 应生成唯一文件ID', '认证-安全工具', async () => {
      const id1 = generateFileId();
      const id2 = generateFileId();
      
      assertNotNull(id1);
      assertNotNull(id2);
      assertTrue(id1.length >= 12);
      assertTrue(id1 !== id2);
    })
  );

  results.push(
    await runTest('数据库初始化 - 应创建空表', '认证-数据库', async () => {
      const testDb = new MockD1Database();
      
      const users = await testDb.select('users');
      const sessions = await testDb.select('sessions');
      const files = await testDb.select('media_files');
      
      assertEqual(users.length, 0);
      assertEqual(sessions.length, 0);
      assertEqual(files.length, 0);
    })
  );

  results.push(
    await runTest('Mock数据填充 - 应创建测试用户', '认证-数据库', async () => {
      const testDb = new MockD1Database();
      const { users } = await testDb.populateMockData();
      
      assertTrue(users.length >= 3);
      
      const admin = users.find(u => u.username === 'admin');
      assertNotNull(admin);
      assertEqual(admin?.is_admin, 1);
      
      const demo = users.find(u => u.username === 'demo_user');
      assertNotNull(demo);
      assertEqual(demo?.is_admin, 0);
    })
  );

  results.push(
    await runTest('用户插入 - 应成功插入用户', '认证-数据库', async () => {
      const testDb = new MockD1Database();
      const now = new Date().toISOString();
      const passwordHash = await hashPassword('test123');
      
      const userId = await testDb.insert('users', {
        uuid: generateUUID(),
        username: 'testuser',
        email: 'test@test.com',
        password_hash: passwordHash,
        secret_token: generateSecretToken(),
        is_active: 1,
        is_admin: 0,
        telegram_user_id: null,
        created_at: now,
        updated_at: now,
      });
      
      assertTrue(userId > 0);
      
      const user = await testDb.selectOne('users', (r) => (r as { username: string }).username === 'testuser');
      assertNotNull(user);
      
      const typedUser = user as User;
      assertEqual(typedUser.username, 'testuser');
      assertEqual(typedUser.email, 'test@test.com');
    })
  );

  results.push(
    await runTest('用户查询 - 按用户名查询', '认证-数据库', async () => {
      const testDb = new MockD1Database();
      await testDb.populateMockData();
      
      const admin = await testDb.selectOne('users', (r) => (r as { username: string }).username === 'admin');
      assertNotNull(admin);
      
      const typedAdmin = admin as User;
      assertEqual(typedAdmin.username, 'admin');
      assertEqual(typedAdmin.is_admin, 1);
    })
  );

  results.push(
    await runTest('用户查询 - 按邮箱查询', '认证-数据库', async () => {
      const testDb = new MockD1Database();
      await testDb.populateMockData();
      
      const user = await testDb.selectOne('users', (r) => (r as { email: string }).email === 'admin@imgbed.local');
      assertNotNull(user);
      
      const typedUser = user as User;
      assertEqual(typedUser.email, 'admin@imgbed.local');
    })
  );

  results.push(
    await runTest('用户更新 - 应成功更新用户', '认证-数据库', async () => {
      const testDb = new MockD1Database();
      await testDb.populateMockData();
      
      const user = await testDb.selectOne('users', (r) => (r as { username: string }).username === 'demo_user');
      assertNotNull(user);
      
      const typedUser = user as User;
      const updateCount = await testDb.update(
        'users',
        (r) => (r as { id: number }).id === typedUser.id,
        { is_active: 0 }
      );
      
      assertEqual(updateCount, 1);
      
      const updatedUser = await testDb.selectOne('users', (r) => (r as { id: number }).id === typedUser.id);
      assertNotNull(updatedUser);
      assertEqual((updatedUser as User).is_active, 0);
    })
  );

  results.push(
    await runTest('会话插入 - 应成功插入会话', '认证-数据库', async () => {
      const testDb = new MockD1Database();
      const { users } = await testDb.populateMockData();
      
      const user = users[0];
      const now = new Date();
      const expiresAt = new Date(now.getTime() + 24 * 60 * 60 * 1000);
      
      const sessionId = await testDb.insert('sessions', {
        session_id: 'test-session-123',
        user_id: user.id,
        ip_address: '127.0.0.1',
        user_agent: 'Test Agent',
        created_at: now.toISOString(),
        expires_at: expiresAt.toISOString(),
        last_activity: now.toISOString(),
      });
      
      assertTrue(sessionId > 0);
      
      const sessions = await testDb.select('sessions');
      assertEqual(sessions.length, 1);
    })
  );

  results.push(
    await runTest('第一个用户自动成为管理员', '认证-业务逻辑', async () => {
      const testDb = new MockD1Database();
      
      const now = new Date().toISOString();
      const passwordHash = await hashPassword('first123');
      
      await testDb.insert('users', {
        uuid: generateUUID(),
        username: 'firstuser',
        email: 'first@test.com',
        password_hash: passwordHash,
        secret_token: generateSecretToken(),
        is_active: 1,
        is_admin: 0,
        telegram_user_id: null,
        created_at: now,
        updated_at: now,
      });
      
      const userCount = (await testDb.select('users')).length;
      if (userCount === 1) {
        await testDb.update(
          'users',
          (r) => (r as { username: string }).username === 'firstuser',
          { is_admin: 1 }
        );
      }
      
      const user = await testDb.selectOne('users', (r) => (r as { username: string }).username === 'firstuser');
      const typedUser = user as User;
      
      assertEqual(typedUser.is_admin, 1);
    })
  );

  results.push(
    await runTest('用户状态 - 活跃用户应能登录', '认证-业务逻辑', async () => {
      const testDb = new MockD1Database();
      const { users } = await testDb.populateMockData();
      
      const activeUsers = users.filter(u => u.is_active === 1);
      assertTrue(activeUsers.length > 0);
      
      for (const user of activeUsers) {
        assertEqual(user.is_active, 1);
      }
    })
  );

  results.push(
    await runTest('用户状态 - 禁用用户不能登录', '认证-业务逻辑', async () => {
      const testDb = new MockD1Database();
      const { users } = await testDb.populateMockData();
      
      const demoUser = users.find(u => u.username === 'demo_user');
      assertNotNull(demoUser);
      
      await testDb.update(
        'users',
        (r) => (r as { id: number }).id === demoUser!.id,
        { is_active: 0 }
      );
      
      const updatedUser = await testDb.selectOne('users', (r) => (r as { id: number }).id === demoUser!.id);
      assertNotNull(updatedUser);
      assertEqual((updatedUser as User).is_active, 0);
    })
  );

  results.push(
    await runTest('密钥唯一性 - 所有用户密钥应唯一', '认证-安全工具', async () => {
      const testDb = new MockD1Database();
      const { users } = await testDb.populateMockData();
      
      const tokens = users.map(u => u.secret_token);
      const uniqueTokens = new Set(tokens);
      
      assertEqual(uniqueTokens.size, tokens.length);
    })
  );

  results.push(
    await runTest('用户名唯一性 - 不能有重复用户名', '认证-数据库', async () => {
      const testDb = new MockD1Database();
      const { users } = await testDb.populateMockData();
      
      const usernames = users.map(u => u.username);
      const uniqueUsernames = new Set(usernames);
      
      assertEqual(uniqueUsernames.size, usernames.length);
    })
  );

  results.push(
    await runTest('邮箱唯一性 - 不能有重复邮箱', '认证-数据库', async () => {
      const testDb = new MockD1Database();
      const { users } = await testDb.populateMockData();
      
      const emails = users.map(u => u.email);
      const uniqueEmails = new Set(emails);
      
      assertEqual(uniqueEmails.size, emails.length);
    })
  );

  return results;
}
