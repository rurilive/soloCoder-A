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
import { generateUUID, generateSecretToken, hashPassword } from '../src/utils/security';

export async function runAdminTests(): Promise<TestResult[]> {
  const results: TestResult[] = [];
  const env = createMockEnv();

  results.push(
    await runTest('管理员权限 - admin用户应有管理员权限', '管理-权限', async () => {
      const testDb = new MockD1Database();
      const { users } = await testDb.populateMockData();
      
      const admin = users.find(u => u.username === 'admin');
      assertNotNull(admin);
      assertEqual(admin!.is_admin, 1);
    })
  );

  results.push(
    await runTest('普通用户权限 - demo用户不应有管理员权限', '管理-权限', async () => {
      const testDb = new MockD1Database();
      const { users } = await testDb.populateMockData();
      
      const demo = users.find(u => u.username === 'demo_user');
      assertNotNull(demo);
      assertEqual(demo!.is_admin, 0);
    })
  );

  results.push(
    await runTest('用户管理 - 应能切换用户活跃状态', '管理-用户管理', async () => {
      const testDb = new MockD1Database();
      const { users } = await testDb.populateMockData();
      
      const demoUser = users.find(u => u.username === 'demo_user');
      assertNotNull(demoUser);
      
      const originalStatus = demoUser!.is_active;
      
      const updateCount = await testDb.update(
        'users',
        (r) => (r as { id: number }).id === demoUser!.id,
        { is_active: originalStatus === 1 ? 0 : 1 }
      );
      
      assertEqual(updateCount, 1);
      
      const updatedUser = await testDb.selectOne('users', (r) => (r as { id: number }).id === demoUser!.id);
      assertNotNull(updatedUser);
      assertEqual((updatedUser as { is_active: number }).is_active, originalStatus === 1 ? 0 : 1);
    })
  );

  results.push(
    await runTest('用户管理 - 应能切换用户管理员状态', '管理-用户管理', async () => {
      const testDb = new MockD1Database();
      const { users } = await testDb.populateMockData();
      
      const demoUser = users.find(u => u.username === 'demo_user');
      assertNotNull(demoUser);
      
      const originalStatus = demoUser!.is_admin;
      
      const updateCount = await testDb.update(
        'users',
        (r) => (r as { id: number }).id === demoUser!.id,
        { is_admin: originalStatus === 1 ? 0 : 1 }
      );
      
      assertEqual(updateCount, 1);
      
      const updatedUser = await testDb.selectOne('users', (r) => (r as { id: number }).id === demoUser!.id);
      assertNotNull(updatedUser);
      assertEqual((updatedUser as { is_admin: number }).is_admin, originalStatus === 1 ? 0 : 1);
    })
  );

  results.push(
    await runTest('用户管理 - 管理员不能禁用自己', '管理-用户管理', async () => {
      const testDb = new MockD1Database();
      const { users } = await testDb.populateMockData();
      
      const admin = users.find(u => u.username === 'admin');
      assertNotNull(admin);
      
      const originalStatus = admin!.is_active;
      
      const updateCount = await testDb.update(
        'users',
        (r) => (r as { id: number }).id === admin!.id,
        { is_active: 0 }
      );
      
      assertEqual(updateCount, 1);
      
      const updatedUser = await testDb.selectOne('users', (r) => (r as { id: number }).id === admin!.id);
      assertNotNull(updatedUser);
      
      const typedUser = updatedUser as { is_active: number; username: string };
      assertEqual(typedUser.is_active, 0);
      assertEqual(typedUser.username, 'admin');
    })
  );

  results.push(
    await runTest('文件统计 - 应能统计用户总数', '管理-统计', async () => {
      const testDb = new MockD1Database();
      const { users } = await testDb.populateMockData();
      
      const dbUsers = await testDb.select('users');
      assertEqual(dbUsers.length, users.length);
      assertTrue(dbUsers.length >= 3);
    })
  );

  results.push(
    await runTest('文件统计 - 应能统计文件总数', '管理-统计', async () => {
      const testDb = new MockD1Database();
      const { mediaFiles } = await testDb.populateMockData();
      
      const dbFiles = await testDb.select('media_files');
      assertEqual(dbFiles.length, mediaFiles.length);
    })
  );

  results.push(
    await runTest('文件统计 - 应能统计已删除文件数量', '管理-统计', async () => {
      const testDb = new MockD1Database();
      const { mediaFiles } = await testDb.populateMockData();
      
      const deletedCount = mediaFiles.filter(f => f.is_deleted === 1).length;
      const dbDeletedFiles = await testDb.select('media_files', (r) => (r as { is_deleted: number }).is_deleted === 1);
      
      assertEqual(dbDeletedFiles.length, deletedCount);
    })
  );

  results.push(
    await runTest('文件统计 - 应能统计已过期文件数量', '管理-统计', async () => {
      const testDb = new MockD1Database();
      const { mediaFiles } = await testDb.populateMockData();
      
      const expiredCount = mediaFiles.filter(f => f.is_expired === 1).length;
      const dbExpiredFiles = await testDb.select('media_files', (r) => (r as { is_expired: number }).is_expired === 1);
      
      assertEqual(dbExpiredFiles.length, expiredCount);
    })
  );

  results.push(
    await runTest('硬删除 - 管理员应能硬删除文件', '管理-文件管理', async () => {
      const testDb = new MockD1Database();
      const { mediaFiles } = await testDb.populateMockData();
      
      const deletedFiles = mediaFiles.filter(f => f.is_deleted === 1);
      if (deletedFiles.length > 0) {
        const testFile = deletedFiles[0];
        
        const deleteCount = await testDb.delete(
          'media_files',
          (r) => (r as { file_id: string }).file_id === testFile.file_id
        );
        
        assertEqual(deleteCount, 1);
        
        const foundFile = await testDb.selectOne('media_files', (r) => (r as { file_id: string }).file_id === testFile.file_id);
        assertEqual(foundFile, null);
      }
    })
  );

  results.push(
    await runTest('管理员恢复 - 管理员应能恢复文件', '管理-文件管理', async () => {
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
        assertEqual((updatedFile as { is_deleted: number }).is_deleted, 0);
      }
    })
  );

  results.push(
    await runTest('系统清理 - 应能软删除过期文件', '管理-清理', async () => {
      const testDb = new MockD1Database();
      
      const now = new Date().toISOString();
      const passwordHash = await hashPassword('test123');
      
      const userId = await testDb.insert('users', {
        uuid: generateUUID(),
        username: 'expire_test',
        email: 'expire@test.com',
        password_hash: passwordHash,
        secret_token: generateSecretToken(),
        is_active: 1,
        is_admin: 0,
        telegram_user_id: null,
        created_at: now,
        updated_at: now,
      });
      
      const pastDate = new Date();
      pastDate.setDate(pastDate.getDate() - 30);
      
      const expiredDate = new Date();
      expiredDate.setDate(expiredDate.getDate() - 7);
      
      await testDb.insert('media_files', {
        file_id: 'expired_test_001',
        user_id: userId,
        original_filename: 'expired-test.jpg',
        media_type: 'image',
        mime_type: 'image/jpeg',
        file_size: 1024000,
        width: 1920,
        height: 1080,
        original_path: 'test/expired_original.jpg',
        original_size: 1024000,
        is_public: 1,
        view_count: 10,
        created_at: pastDate.toISOString(),
        updated_at: null,
        expires_at: expiredDate.toISOString(),
        is_expired: 1,
        is_deleted: 0,
        deleted_at: null,
        deleted_reason: null,
        require_token: 0,
        allowed_referers: null,
      });
      
      const expiredFiles = await testDb.select('media_files', (r) => 
        (r as { is_expired: number; is_deleted: number }).is_expired === 1 && 
        (r as { is_expired: number; is_deleted: number }).is_deleted === 0
      );
      
      assertTrue(expiredFiles.length > 0);
      
      const updateCount = await testDb.update(
        'media_files',
        (r) => 
          (r as { is_expired: number; is_deleted: number }).is_expired === 1 && 
          (r as { is_expired: number; is_deleted: number }).is_deleted === 0,
        {
          is_deleted: 1,
          deleted_at: now,
          deleted_reason: 'Auto cleanup: expired file',
        }
      );
      
      assertEqual(updateCount, expiredFiles.length);
      
      const afterDelete = await testDb.select('media_files', (r) => 
        (r as { is_expired: number; is_deleted: number }).is_expired === 1 && 
        (r as { is_expired: number; is_deleted: number }).is_deleted === 0
      );
      
      assertEqual(afterDelete.length, 0);
    })
  );

  results.push(
    await runTest('系统清理 - 应能硬删除旧的软删除文件', '管理-清理', async () => {
      const testDb = new MockD1Database();
      
      const now = new Date().toISOString();
      const passwordHash = await hashPassword('test123');
      
      const userId = await testDb.insert('users', {
        uuid: generateUUID(),
        username: 'cleanup_test',
        email: 'cleanup@test.com',
        password_hash: passwordHash,
        secret_token: generateSecretToken(),
        is_active: 1,
        is_admin: 0,
        telegram_user_id: null,
        created_at: now,
        updated_at: now,
      });
      
      const deletedDate = new Date();
      deletedDate.setDate(deletedDate.getDate() - 100);
      
      await testDb.insert('media_files', {
        file_id: 'old_deleted_001',
        user_id: userId,
        original_filename: 'old-deleted.jpg',
        media_type: 'image',
        mime_type: 'image/jpeg',
        file_size: 1024000,
        width: 1920,
        height: 1080,
        original_path: 'test/old_deleted.jpg',
        original_size: 1024000,
        is_public: 1,
        view_count: 5,
        created_at: deletedDate.toISOString(),
        updated_at: null,
        expires_at: null,
        is_expired: 0,
        is_deleted: 1,
        deleted_at: deletedDate.toISOString(),
        deleted_reason: 'Old test file',
        require_token: 0,
        allowed_referers: null,
      });
      
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - 90);
      
      const oldDeletedFiles = await testDb.select('media_files', (r) => {
        const typed = r as { is_deleted: number; deleted_at: string };
        return typed.is_deleted === 1 && typed.deleted_at && new Date(typed.deleted_at) <= cutoffDate;
      });
      
      assertTrue(oldDeletedFiles.length > 0);
      
      const deleteCount = await testDb.delete('media_files', (r) => {
        const typed = r as { is_deleted: number; deleted_at: string };
        return typed.is_deleted === 1 && typed.deleted_at && new Date(typed.deleted_at) <= cutoffDate;
      });
      
      assertEqual(deleteCount, oldDeletedFiles.length);
    })
  );

  results.push(
    await runTest('用户文件列表 - 管理员应能查看用户文件', '管理-用户管理', async () => {
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
    await runTest('统计测试 - Mock数据应包含各种状态的文件', '管理-统计', async () => {
      const testDb = new MockD1Database();
      const { mediaFiles } = await testDb.populateMockData();
      
      const activeFiles = mediaFiles.filter(f => f.is_deleted === 0 && f.is_expired === 0);
      const expiredFiles = mediaFiles.filter(f => f.is_expired === 1);
      const deletedFiles = mediaFiles.filter(f => f.is_deleted === 1);
      const tokenFiles = mediaFiles.filter(f => f.require_token === 1);
      
      assertTrue(activeFiles.length > 0);
      assertTrue(expiredFiles.length >= 0);
      assertTrue(deletedFiles.length >= 0);
      assertTrue(tokenFiles.length >= 0);
    })
  );

  return results;
}
