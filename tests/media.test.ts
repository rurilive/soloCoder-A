import type { TestResult, MediaType } from './helpers/test-utils';
import {
  createMockEnv,
  runTest,
  assertEqual,
  assertTrue,
  assertFalse,
  assertNotNull,
  MockD1Database,
  MockR2Bucket,
} from './helpers/test-utils';
import { generateUUID, generateSecretToken, generateFileId } from '../src/utils/security';

export async function runMediaTests(): Promise<TestResult[]> {
  const results: TestResult[] = [];
  const env = createMockEnv();
  const db = env.DB as unknown as MockD1Database;

  results.push(
    await runTest('R2存储 - 应能存储文件', '媒体-存储', async () => {
      const bucket = new MockR2Bucket();
      
      const testKey = 'test/test-file.jpg';
      const testContent = 'test content';
      
      const obj = await bucket.put(testKey, testContent);
      
      assertNotNull(obj);
      assertEqual(obj.key, testKey);
      
      const objects = bucket.getObjects();
      assertTrue(objects.has(testKey));
    })
  );

  results.push(
    await runTest('R2存储 - 应能删除文件', '媒体-存储', async () => {
      const bucket = new MockR2Bucket();
      
      const testKey = 'test/test-file.jpg';
      await bucket.put(testKey, 'test content');
      
      assertTrue(bucket.getObjects().has(testKey));
      
      await bucket.delete(testKey);
      
      assertFalse(bucket.getObjects().has(testKey));
    })
  );

  results.push(
    await runTest('媒体文件 - 应能插入图片文件', '媒体-数据库', async () => {
      const testDb = new MockD1Database();
      const { users } = await testDb.populateMockData();
      
      const user = users[0];
      const now = new Date().toISOString();
      const fileId = generateFileId();
      const uuidParts = user.uuid.split('-').slice(0, 2).join('/');
      
      const mediaFileId = await testDb.insert('media_files', {
        file_id: fileId,
        user_id: user.id,
        original_filename: 'test-image.jpg',
        media_type: 'image' as MediaType,
        mime_type: 'image/jpeg',
        file_size: 1024000,
        width: 1920,
        height: 1080,
        original_path: `${uuidParts}/${fileId}_original.jpg`,
        standard_path: `${uuidParts}/${fileId}_standard.jpg`,
        low_path: `${uuidParts}/${fileId}_low.jpg`,
        icon_path: `${uuidParts}/${fileId}_icon.jpg`,
        original_size: 1024000,
        standard_size: 512000,
        low_size: 256000,
        icon_size: 64000,
        telegram_file_id: null,
        telegram_message_id: null,
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
      
      assertTrue(mediaFileId > 0);
      
      const files = await testDb.select('media_files');
      assertTrue(files.length > 0);
    })
  );

  results.push(
    await runTest('媒体文件 - 应能插入视频文件', '媒体-数据库', async () => {
      const testDb = new MockD1Database();
      const { users } = await testDb.populateMockData();
      
      const user = users[0];
      const now = new Date().toISOString();
      const fileId = generateFileId();
      const uuidParts = user.uuid.split('-').slice(0, 2).join('/');
      
      const mediaFileId = await testDb.insert('media_files', {
        file_id: fileId,
        user_id: user.id,
        original_filename: 'test-video.mp4',
        media_type: 'video' as MediaType,
        mime_type: 'video/mp4',
        file_size: 10240000,
        width: null,
        height: null,
        original_path: `${uuidParts}/${fileId}_original.mp4`,
        standard_path: null,
        low_path: null,
        icon_path: null,
        original_size: 10240000,
        standard_size: null,
        low_size: null,
        icon_size: null,
        telegram_file_id: null,
        telegram_message_id: null,
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
      
      assertTrue(mediaFileId > 0);
      
      const file = await testDb.selectOne('media_files', (r) => (r as { file_id: string }).file_id === fileId);
      assertNotNull(file);
      
      const typedFile = file as { media_type: string; width: number | null };
      assertEqual(typedFile.media_type, 'video');
      assertEqual(typedFile.width, null);
    })
  );

  results.push(
    await runTest('媒体文件 - 按用户ID查询', '媒体-数据库', async () => {
      const testDb = new MockD1Database();
      const { users, mediaFiles } = await testDb.populateMockData();
      
      const user = users[0];
      const userFiles = await testDb.select('media_files', (r) => (r as { user_id: number }).user_id === user.id);
      
      assertTrue(userFiles.length >= 0);
      
      for (const f of userFiles) {
        assertEqual((f as { user_id: number }).user_id, user.id);
      }
    })
  );

  results.push(
    await runTest('媒体文件 - 按file_id查询', '媒体-数据库', async () => {
      const testDb = new MockD1Database();
      const { mediaFiles } = await testDb.populateMockData();
      
      if (mediaFiles.length > 0) {
        const testFile = mediaFiles[0];
        const foundFile = await testDb.selectOne('media_files', (r) => (r as { file_id: string }).file_id === testFile.file_id);
        
        assertNotNull(foundFile);
        assertEqual((foundFile as { file_id: string }).file_id, testFile.file_id);
      }
    })
  );

  results.push(
    await runTest('软删除 - 应能软删除文件', '媒体-业务逻辑', async () => {
      const testDb = new MockD1Database();
      const { mediaFiles } = await testDb.populateMockData();
      
      const activeFiles = mediaFiles.filter(f => f.is_deleted === 0);
      if (activeFiles.length > 0) {
        const testFile = activeFiles[0];
        const now = new Date().toISOString();
        
        const updateCount = await testDb.update(
          'media_files',
          (r) => (r as { file_id: string }).file_id === testFile.file_id,
          {
            is_deleted: 1,
            deleted_at: now,
            deleted_reason: 'Test deletion',
          }
        );
        
        assertEqual(updateCount, 1);
        
        const updatedFile = await testDb.selectOne('media_files', (r) => (r as { file_id: string }).file_id === testFile.file_id);
        assertNotNull(updatedFile);
        
        const typedFile = updatedFile as { is_deleted: number; deleted_at: string | null };
        assertEqual(typedFile.is_deleted, 1);
        assertNotNull(typedFile.deleted_at);
      }
    })
  );

  results.push(
    await runTest('恢复文件 - 应能恢复已软删除的文件', '媒体-业务逻辑', async () => {
      const testDb = new MockD1Database();
      const { mediaFiles } = await testDb.populateMockData();
      
      const deletedFiles = mediaFiles.filter(f => f.is_deleted === 1);
      if (deletedFiles.length > 0) {
        const testFile = deletedFiles[0];
        
        const updateCount = await testDb.update(
          'media_files',
          (r) => (r as { file_id: string }).file_id === testFile.file_id,
          {
            is_deleted: 0,
            deleted_at: null,
            deleted_reason: null,
          }
        );
        
        assertEqual(updateCount, 1);
        
        const updatedFile = await testDb.selectOne('media_files', (r) => (r as { file_id: string }).file_id === testFile.file_id);
        assertNotNull(updatedFile);
        
        const typedFile = updatedFile as { is_deleted: number; deleted_at: string | null };
        assertEqual(typedFile.is_deleted, 0);
        assertEqual(typedFile.deleted_at, null);
      }
    })
  );

  results.push(
    await runTest('过期时间 - 应能设置过期时间', '媒体-业务逻辑', async () => {
      const testDb = new MockD1Database();
      const { users } = await testDb.populateMockData();
      
      const user = users[0];
      const now = new Date();
      const expireDate = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
      const fileId = generateFileId();
      const uuidParts = user.uuid.split('-').slice(0, 2).join('/');
      
      await testDb.insert('media_files', {
        file_id: fileId,
        user_id: user.id,
        original_filename: 'expiring-image.jpg',
        media_type: 'image' as MediaType,
        mime_type: 'image/jpeg',
        file_size: 1024000,
        width: 1920,
        height: 1080,
        original_path: `${uuidParts}/${fileId}_original.jpg`,
        standard_path: null,
        low_path: null,
        icon_path: null,
        original_size: 1024000,
        standard_size: null,
        low_size: null,
        icon_size: null,
        telegram_file_id: null,
        telegram_message_id: null,
        is_public: 1,
        view_count: 0,
        created_at: now.toISOString(),
        updated_at: null,
        expires_at: expireDate.toISOString(),
        is_expired: 0,
        is_deleted: 0,
        deleted_at: null,
        deleted_reason: null,
        require_token: 0,
        allowed_referers: null,
      });
      
      const file = await testDb.selectOne('media_files', (r) => (r as { file_id: string }).file_id === fileId);
      assertNotNull(file);
      
      const typedFile = file as { expires_at: string | null; is_expired: number };
      assertNotNull(typedFile.expires_at);
      assertEqual(typedFile.is_expired, 0);
    })
  );

  results.push(
    await runTest('过期状态 - 已过期文件应标记为过期', '媒体-业务逻辑', async () => {
      const testDb = new MockD1Database();
      const { mediaFiles } = await testDb.populateMockData();
      
      const expiredFiles = mediaFiles.filter(f => f.is_expired === 1);
      
      for (const file of expiredFiles) {
        assertEqual(file.is_expired, 1);
        assertNotNull(file.expires_at);
      }
    })
  );

  results.push(
    await runTest('访问计数 - 应能增加访问计数', '媒体-业务逻辑', async () => {
      const testDb = new MockD1Database();
      const { mediaFiles } = await testDb.populateMockData();
      
      const activeFiles = mediaFiles.filter(f => f.is_deleted === 0 && f.is_expired === 0);
      if (activeFiles.length > 0) {
        const testFile = activeFiles[0];
        const originalViewCount = testFile.view_count;
        
        const updateCount = await testDb.update(
          'media_files',
          (r) => (r as { file_id: string }).file_id === testFile.file_id,
          {
            view_count: originalViewCount + 1,
          }
        );
        
        assertEqual(updateCount, 1);
        
        const updatedFile = await testDb.selectOne('media_files', (r) => (r as { file_id: string }).file_id === testFile.file_id);
        assertNotNull(updatedFile);
        assertEqual((updatedFile as { view_count: number }).view_count, originalViewCount + 1);
      }
    })
  );

  results.push(
    await runTest('令牌访问 - 应能设置require_token', '媒体-访问控制', async () => {
      const testDb = new MockD1Database();
      const { users } = await testDb.populateMockData();
      
      const user = users[0];
      const now = new Date().toISOString();
      const fileId = generateFileId();
      const uuidParts = user.uuid.split('-').slice(0, 2).join('/');
      
      await testDb.insert('media_files', {
        file_id: fileId,
        user_id: user.id,
        original_filename: 'protected-image.jpg',
        media_type: 'image' as MediaType,
        mime_type: 'image/jpeg',
        file_size: 1024000,
        width: 1920,
        height: 1080,
        original_path: `${uuidParts}/${fileId}_original.jpg`,
        standard_path: null,
        low_path: null,
        icon_path: null,
        original_size: 1024000,
        standard_size: null,
        low_size: null,
        icon_size: null,
        telegram_file_id: null,
        telegram_message_id: null,
        is_public: 1,
        view_count: 0,
        created_at: now,
        updated_at: null,
        expires_at: null,
        is_expired: 0,
        is_deleted: 0,
        deleted_at: null,
        deleted_reason: null,
        require_token: 1,
        allowed_referers: 'example.com, test.com',
      });
      
      const file = await testDb.selectOne('media_files', (r) => (r as { file_id: string }).file_id === fileId);
      assertNotNull(file);
      
      const typedFile = file as { require_token: number; allowed_referers: string | null };
      assertEqual(typedFile.require_token, 1);
      assertNotNull(typedFile.allowed_referers);
      assertTrue(typedFile.allowed_referers!.includes('example.com'));
    })
  );

  results.push(
    await runTest('引用者限制 - 应能设置allowed_referers', '媒体-访问控制', async () => {
      const testDb = new MockD1Database();
      const { mediaFiles } = await testDb.populateMockData();
      
      const tokenFiles = mediaFiles.filter(f => f.require_token === 1);
      
      for (const file of tokenFiles) {
        if (file.allowed_referers) {
          assertTrue(file.allowed_referers.length > 0);
          assertTrue(file.allowed_referers.includes(','));
        }
      }
    })
  );

  results.push(
    await runTest('图片质量 - 图片应有多种质量版本', '媒体-业务逻辑', async () => {
      const testDb = new MockD1Database();
      const { mediaFiles } = await testDb.populateMockData();
      
      const imageFiles = mediaFiles.filter(f => f.media_type === 'image');
      
      for (const file of imageFiles) {
        assertEqual(file.media_type, 'image');
        assertNotNull(file.original_path);
        
        if (file.standard_path) {
          assertTrue(file.standard_path.includes('standard'));
        }
        if (file.low_path) {
          assertTrue(file.low_path.includes('low'));
        }
        if (file.icon_path) {
          assertTrue(file.icon_path.includes('icon'));
        }
      }
    })
  );

  results.push(
    await runTest('视频文件 - 视频只有原始版本', '媒体-业务逻辑', async () => {
      const testDb = new MockD1Database();
      const { mediaFiles } = await testDb.populateMockData();
      
      const videoFiles = mediaFiles.filter(f => f.media_type === 'video');
      
      for (const file of videoFiles) {
        assertEqual(file.media_type, 'video');
        assertNotNull(file.original_path);
        assertEqual(file.standard_path, null);
        assertEqual(file.low_path, null);
        assertEqual(file.icon_path, null);
      }
    })
  );

  results.push(
    await runTest('文件ID唯一性 - 所有文件ID应唯一', '媒体-数据库', async () => {
      const testDb = new MockD1Database();
      const { mediaFiles } = await testDb.populateMockData();
      
      const fileIds = mediaFiles.map(f => f.file_id);
      const uniqueFileIds = new Set(fileIds);
      
      assertEqual(uniqueFileIds.size, fileIds.length);
    })
  );

  results.push(
    await runTest('文件统计 - 应能统计用户文件数量', '媒体-业务逻辑', async () => {
      const testDb = new MockD1Database();
      const { users, mediaFiles } = await testDb.populateMockData();
      
      for (const user of users) {
        const userFiles = mediaFiles.filter(f => f.user_id === user.id);
        const dbUserFiles = await testDb.select('media_files', (r) => (r as { user_id: number }).user_id === user.id);
        
        assertEqual(dbUserFiles.length, userFiles.length);
      }
    })
  );

  results.push(
    await runTest('Telegram存储 - 应能存储Telegram文件ID', '媒体-Telegram集成', async () => {
      const testDb = new MockD1Database();
      const { users } = await testDb.populateMockData();
      
      const user = users[0];
      const now = new Date().toISOString();
      const fileId = generateFileId();
      const uuidParts = user.uuid.split('-').slice(0, 2).join('/');
      
      await testDb.insert('media_files', {
        file_id: fileId,
        user_id: user.id,
        original_filename: 'telegram-upload.jpg',
        media_type: 'image' as MediaType,
        mime_type: 'image/jpeg',
        file_size: 1024000,
        width: 1920,
        height: 1080,
        original_path: `telegram:ABC123XYZ`,
        standard_path: null,
        low_path: null,
        icon_path: null,
        original_size: 1024000,
        standard_size: null,
        low_size: null,
        icon_size: null,
        telegram_file_id: 'ABC123XYZ',
        telegram_message_id: 12345,
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
      };
      
      assertNotNull(typedFile.telegram_file_id);
      assertEqual(typedFile.telegram_file_id, 'ABC123XYZ');
      assertNotNull(typedFile.telegram_message_id);
      assertTrue(typedFile.original_path.startsWith('telegram:'));
    })
  );

  return results;
}
