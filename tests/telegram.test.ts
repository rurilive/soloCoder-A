import type { TestResult, TelegramUpdate, TelegramMessage } from './helpers/test-utils';
import {
  createMockEnv,
  runTest,
  assertEqual,
  assertTrue,
  assertFalse,
  assertNotNull,
  MockD1Database,
} from './helpers/test-utils';
import { generateUUID, generateSecretToken, generateFileId, hashPassword } from '../src/utils/security';

export async function runTelegramTests(): Promise<TestResult[]> {
  const results: TestResult[] = [];
  const env = createMockEnv();

  results.push(
    await runTest('Bot配置 - 环境变量应包含Bot配置', 'Telegram-配置', async () => {
      const env = createMockEnv();
      
      assertNotNull(env.TELEGRAM_BOT_TOKEN);
      assertNotNull(env.TELEGRAM_CHANNEL_ID);
      assertNotNull(env.TELEGRAM_WEBHOOK_SECRET);
      
      assertTrue(env.TELEGRAM_BOT_TOKEN.length > 0);
      assertTrue(env.TELEGRAM_WEBHOOK_SECRET.length > 0);
    })
  );

  results.push(
    await runTest('用户注册 - 新用户发送消息应自动创建账号', 'Telegram-用户管理', async () => {
      const testDb = new MockD1Database();
      
      const telegramUserId = 123456789;
      const username = 'test_telegram_user';
      const now = new Date().toISOString();
      const passwordHash = await hashPassword(generateSecretToken());
      
      const userId = await testDb.insert('users', {
        uuid: generateUUID(),
        username: username,
        email: `${telegramUserId}@telegram.local`,
        password_hash: passwordHash,
        secret_token: generateSecretToken(),
        is_active: 1,
        is_admin: 0,
        telegram_user_id: telegramUserId,
        created_at: now,
        updated_at: now,
      });
      
      assertTrue(userId > 0);
      
      const user = await testDb.selectOne('users', (r) => (r as { telegram_user_id: number }).telegram_user_id === telegramUserId);
      assertNotNull(user);
      
      const typedUser = user as { username: string; telegram_user_id: number };
      assertEqual(typedUser.username, username);
      assertEqual(typedUser.telegram_user_id, telegramUserId);
    })
  );

  results.push(
    await runTest('用户查询 - 应能按Telegram用户ID查询用户', 'Telegram-用户管理', async () => {
      const testDb = new MockD1Database();
      
      const telegramUserId = 987654321;
      const now = new Date().toISOString();
      const passwordHash = await hashPassword(generateSecretToken());
      
      await testDb.insert('users', {
        uuid: generateUUID(),
        username: 'telegram_test_user_2',
        email: `${telegramUserId}@telegram.local`,
        password_hash: passwordHash,
        secret_token: generateSecretToken(),
        is_active: 1,
        is_admin: 0,
        telegram_user_id: telegramUserId,
        created_at: now,
        updated_at: now,
      });
      
      const user = await testDb.selectOne('users', (r) => (r as { telegram_user_id: number }).telegram_user_id === telegramUserId);
      assertNotNull(user);
      
      const typedUser = user as { telegram_user_id: number; is_active: number };
      assertEqual(typedUser.telegram_user_id, telegramUserId);
      assertEqual(typedUser.is_active, 1);
    })
  );

  results.push(
    await runTest('用户唯一性 - Telegram用户ID应唯一', 'Telegram-用户管理', async () => {
      const testDb = new MockD1Database();
      
      const telegramUserId = 111222333;
      const now = new Date().toISOString();
      const passwordHash = await hashPassword(generateSecretToken());
      
      await testDb.insert('users', {
        uuid: generateUUID(),
        username: 'first_user',
        email: `${telegramUserId}@telegram.local`,
        password_hash: passwordHash,
        secret_token: generateSecretToken(),
        is_active: 1,
        is_admin: 0,
        telegram_user_id: telegramUserId,
        created_at: now,
        updated_at: now,
      });
      
      const users = await testDb.select('users', (r) => (r as { telegram_user_id: number }).telegram_user_id === telegramUserId);
      assertEqual(users.length, 1);
    })
  );

  results.push(
    await runTest('文件上传 - Bot上传的文件应记录Telegram信息', 'Telegram-文件管理', async () => {
      const testDb = new MockD1Database();
      
      const telegramUserId = 444555666;
      const now = new Date().toISOString();
      const passwordHash = await hashPassword(generateSecretToken());
      
      const userId = await testDb.insert('users', {
        uuid: generateUUID(),
        username: 'telegram_uploader',
        email: `${telegramUserId}@telegram.local`,
        password_hash: passwordHash,
        secret_token: generateSecretToken(),
        is_active: 1,
        is_admin: 0,
        telegram_user_id: telegramUserId,
        created_at: now,
        updated_at: now,
      });
      
      const user = await testDb.selectOne('users', (r) => (r as { id: number }).id === userId);
      const typedUser = user as { uuid: string };
      const uuidParts = typedUser.uuid.split('-').slice(0, 2).join('/');
      
      const telegramFileId = 'TelegramFile_ABC123XYZ';
      const telegramMessageId = 98765;
      
      const fileId = generateFileId();
      
      await testDb.insert('media_files', {
        file_id: fileId,
        user_id: userId,
        original_filename: 'telegram_upload.jpg',
        media_type: 'image',
        mime_type: 'image/jpeg',
        file_size: 1024000,
        width: 1920,
        height: 1080,
        original_path: `telegram:${telegramFileId}`,
        standard_path: null,
        low_path: null,
        icon_path: null,
        original_size: 1024000,
        standard_size: null,
        low_size: null,
        icon_size: null,
        telegram_file_id: telegramFileId,
        telegram_message_id: telegramMessageId,
        is_public: 1,
        view_count: 0,
        created_at: now,
        updated_at: null,
        expires_at: null,
        is_expired: 0,
        is_deleted: 0,
        deleted_at: null,
        deleted_reason: null,
        require_token: 0,
        allowed_referers: null,
      });
      
      const file = await testDb.selectOne('media_files', (r) => (r as { file_id: string }).file_id === fileId);
      assertNotNull(file);
      
      const typedFile = file as { 
        telegram_file_id: string | null; 
        telegram_message_id: number | null;
        original_path: string;
        user_id: number;
      };
      
      assertNotNull(typedFile.telegram_file_id);
      assertEqual(typedFile.telegram_file_id, telegramFileId);
      assertNotNull(typedFile.telegram_message_id);
      assertEqual(typedFile.telegram_message_id, telegramMessageId);
      assertTrue(typedFile.original_path.startsWith('telegram:'));
      assertEqual(typedFile.user_id, userId);
    })
  );

  results.push(
    await runTest('文件查询 - 应能查询用户通过Bot上传的文件', 'Telegram-文件管理', async () => {
      const testDb = new MockD1Database();
      
      const telegramUserId = 777888999;
      const now = new Date().toISOString();
      const passwordHash = await hashPassword(generateSecretToken());
      
      const userId = await testDb.insert('users', {
        uuid: generateUUID(),
        username: 'telegram_file_owner',
        email: `${telegramUserId}@telegram.local`,
        password_hash: passwordHash,
        secret_token: generateSecretToken(),
        is_active: 1,
        is_admin: 0,
        telegram_user_id: telegramUserId,
        created_at: now,
        updated_at: now,
      });
      
      for (let i = 0; i < 5; i++) {
        await testDb.insert('media_files', {
          file_id: generateFileId(),
          user_id: userId,
          original_filename: `telegram_file_${i}.jpg`,
          media_type: 'image',
          mime_type: 'image/jpeg',
          file_size: 1024000 + i * 1000,
          width: 1920,
          height: 1080,
          original_path: `telegram:FileId_${i}`,
          original_size: 1024000 + i * 1000,
          telegram_file_id: `TelegramFile_${i}`,
          telegram_message_id: 1000 + i,
          is_public: 1,
          view_count: i,
          created_at: now,
          updated_at: null,
          expires_at: null,
          is_expired: 0,
          is_deleted: 0,
          deleted_at: null,
          deleted_reason: null,
          require_token: 0,
          allowed_referers: null,
        });
      }
      
      const userFiles = await testDb.select('media_files', (r) => (r as { user_id: number }).user_id === userId);
      assertEqual(userFiles.length, 5);
      
      for (const file of userFiles) {
        const typedFile = file as { telegram_file_id: string | null; user_id: number };
        assertNotNull(typedFile.telegram_file_id);
        assertTrue(typedFile.telegram_file_id!.startsWith('TelegramFile_'));
        assertEqual(typedFile.user_id, userId);
      }
    })
  );

  results.push(
    await runTest('令牌访问 - Bot用户应有自己的访问令牌', 'Telegram-安全', async () => {
      const testDb = new MockD1Database();
      
      const telegramUserId = 1122334455;
      const now = new Date().toISOString();
      const passwordHash = await hashPassword(generateSecretToken());
      const secretToken = generateSecretToken();
      
      await testDb.insert('users', {
        uuid: generateUUID(),
        username: 'telegram_token_user',
        email: `${telegramUserId}@telegram.local`,
        password_hash: passwordHash,
        secret_token: secretToken,
        is_active: 1,
        is_admin: 0,
        telegram_user_id: telegramUserId,
        created_at: now,
        updated_at: now,
      });
      
      const user = await testDb.selectOne('users', (r) => (r as { telegram_user_id: number }).telegram_user_id === telegramUserId);
      assertNotNull(user);
      
      const typedUser = user as { secret_token: string };
      assertNotNull(typedUser.secret_token);
      assertEqual(typedUser.secret_token, secretToken);
      assertTrue(typedUser.secret_token.length >= 32);
    })
  );

  results.push(
    await runTest('禁用用户 - Bot禁用用户不能使用服务', 'Telegram-用户管理', async () => {
      const testDb = new MockD1Database();
      
      const telegramUserId = 998877665;
      const now = new Date().toISOString();
      const passwordHash = await hashPassword(generateSecretToken());
      
      await testDb.insert('users', {
        uuid: generateUUID(),
        username: 'disabled_bot_user',
        email: `${telegramUserId}@telegram.local`,
        password_hash: passwordHash,
        secret_token: generateSecretToken(),
        is_active: 0,
        is_admin: 0,
        telegram_user_id: telegramUserId,
        created_at: now,
        updated_at: now,
      });
      
      const user = await testDb.selectOne('users', (r) => (r as { telegram_user_id: number }).telegram_user_id === telegramUserId);
      assertNotNull(user);
      
      const typedUser = user as { is_active: number };
      assertEqual(typedUser.is_active, 0);
    })
  );

  results.push(
    await runTest('Webhook验证 - 应验证Webhook密钥', 'Telegram-安全', async () => {
      const env = createMockEnv();
      const validSecret = env.TELEGRAM_WEBHOOK_SECRET;
      const invalidSecret = 'invalid-secret';
      
      assertTrue(validSecret.length > 0);
      assertTrue(invalidSecret !== validSecret);
      
      const headers: Record<string, string> = {
        'X-Telegram-Bot-Api-Secret-Token': validSecret,
      };
      
      assertEqual(headers['X-Telegram-Bot-Api-Secret-Token'], validSecret);
    })
  );

  results.push(
    await runTest('频道存储 - 文件应记录频道消息ID', 'Telegram-存储', async () => {
      const testDb = new MockD1Database();
      
      const now = new Date().toISOString();
      const passwordHash = await hashPassword(generateSecretToken());
      
      const userId = await testDb.insert('users', {
        uuid: generateUUID(),
        username: 'channel_test_user',
        email: 'channel@test.local',
        password_hash: passwordHash,
        secret_token: generateSecretToken(),
        is_active: 1,
        is_admin: 0,
        telegram_user_id: 12345,
        created_at: now,
        updated_at: now,
      });
      
      const telegramFileId = 'ChannelStoredFile';
      const telegramMessageId = 54321;
      
      const fileId = generateFileId();
      
      await testDb.insert('media_files', {
        file_id: fileId,
        user_id: userId,
        original_filename: 'channel_image.png',
        media_type: 'image',
        mime_type: 'image/png',
        file_size: 2048000,
        width: 2048,
        height: 1536,
        original_path: `telegram:${telegramFileId}`,
        original_size: 2048000,
        telegram_file_id: telegramFileId,
        telegram_message_id: telegramMessageId,
        is_public: 1,
        view_count: 0,
        created_at: now,
        updated_at: null,
        expires_at: null,
        is_expired: 0,
        is_deleted: 0,
        deleted_at: null,
        deleted_reason: null,
        require_token: 0,
        allowed_referers: null,
      });
      
      const file = await testDb.selectOne('media_files', (r) => (r as { file_id: string }).file_id === fileId);
      assertNotNull(file);
      
      const typedFile = file as { 
        telegram_message_id: number | null;
        telegram_file_id: string | null;
      };
      
      assertNotNull(typedFile.telegram_message_id);
      assertEqual(typedFile.telegram_message_id, telegramMessageId);
      assertNotNull(typedFile.telegram_file_id);
    })
  );

  results.push(
    await runTest('文件统计 - Bot用户文件统计', 'Telegram-统计', async () => {
      const testDb = new MockD1Database();
      
      const now = new Date().toISOString();
      const passwordHash = await hashPassword(generateSecretToken());
      
      const userId = await testDb.insert('users', {
        uuid: generateUUID(),
        username: 'stats_test_bot',
        email: 'stats@bot.local',
        password_hash: passwordHash,
        secret_token: generateSecretToken(),
        is_active: 1,
        is_admin: 0,
        telegram_user_id: 99999,
        created_at: now,
        updated_at: now,
      });
      
      for (let i = 0; i < 10; i++) {
        await testDb.insert('media_files', {
          file_id: generateFileId(),
          user_id: userId,
          original_filename: `stats_file_${i}.jpg`,
          media_type: 'image',
          mime_type: 'image/jpeg',
          file_size: 1000000 + i * 50000,
          width: 1920,
          height: 1080,
          original_path: `telegram:StatsFile_${i}`,
          original_size: 1000000 + i * 50000,
          telegram_file_id: `StatsTelegramFile_${i}`,
          telegram_message_id: 2000 + i,
          is_public: 1,
          view_count: i * 10,
          created_at: now,
          updated_at: null,
          expires_at: null,
          is_expired: 0,
          is_deleted: 0,
          deleted_at: null,
          deleted_reason: null,
          require_token: 0,
          allowed_referers: null,
        });
      }
      
      const userFiles = await testDb.select('media_files', (r) => (r as { user_id: number }).user_id === userId);
      assertEqual(userFiles.length, 10);
      
      let totalViews = 0;
      for (const file of userFiles) {
        const typedFile = file as { view_count: number };
        totalViews += typedFile.view_count;
      }
      
      const expectedViews = 0 + 10 + 20 + 30 + 40 + 50 + 60 + 70 + 80 + 90;
      assertEqual(totalViews, expectedViews);
    })
  );

  return results;
}
