import { Hono } from 'hono';
import type { Env, User, MediaFile, ApiResponse } from '../types';
import { UserRepository, MediaFileRepository } from '../repositories';
import { requireAdmin, getCurrentUser } from '../middleware/auth';
import { generateUUID, generateSecretToken, hashPassword } from '../utils/security';

const admin = new Hono<{ Bindings: Env }>();

function getFileUrl(c: Context<{ Bindings: Env }>, fileId: string, quality: string): string {
  const url = new URL(c.req.url);
  return `${url.origin}/file/${fileId}/${quality}`;
}

admin.get('/admin', requireAdmin, async (c) => {
  const user = c.get('user') as User;
  const userRepo = new UserRepository(c.env.DB);
  const mediaRepo = new MediaFileRepository(c.env.DB);

  const userCount = await userRepo.count();
  const fileCount = await mediaRepo.count();
  const deletedCount = await mediaRepo.countDeleted();
  const expiredCount = await mediaRepo.countExpired();

  const users = await userRepo.list(100, 0);
  const files = await mediaRepo.list(200, 0);

  const now = new Date();
  for (const f of files) {
    if (f.is_expired === 0 && f.expires_at) {
      if (now > new Date(f.expires_at)) {
        await mediaRepo.update(f.id, { is_expired: 1 });
        f.is_expired = 1;
      }
    }
  }

  return c.html(await renderAdminDashboard(c, user, {
    userCount,
    fileCount,
    deletedCount,
    expiredCount,
    users,
    files,
  }));
});

admin.get('/admin/users/:userId/files', requireAdmin, async (c) => {
  const user = c.get('user') as User;
  const userId = parseInt(c.req.param('userId'));
  
  const userRepo = new UserRepository(c.env.DB);
  const mediaRepo = new MediaFileRepository(c.env.DB);

  const targetUser = await userRepo.findById(userId);
  if (!targetUser) {
    return c.json({ error: 'User not found' } as ApiResponse, 404);
  }

  const files = await mediaRepo.findByUserId(userId, 1000, 0);
  
  const now = new Date();
  for (const f of files) {
    if (f.is_expired === 0 && f.expires_at) {
      if (now > new Date(f.expires_at)) {
        await mediaRepo.update(f.id, { is_expired: 1 });
        f.is_expired = 1;
      }
    }
  }

  return c.html(await renderAdminUserFiles(c, user, targetUser, files));
});

admin.post('/api/admin/users/:userId/toggle-active', requireAdmin, async (c) => {
  const currentUser = c.get('user') as User;
  const userId = parseInt(c.req.param('userId'));

  const userRepo = new UserRepository(c.env.DB);
  const targetUser = await userRepo.findById(userId);

  if (!targetUser) {
    return c.json({ error: 'User not found' } as ApiResponse, 404);
  }

  if (targetUser.id === currentUser.id) {
    return c.json({ error: 'Cannot toggle your own account' } as ApiResponse, 400);
  }

  const newStatus = targetUser.is_active !== 1;
  await userRepo.update(targetUser.id, { is_active: newStatus ? 1 : 0 });

  return c.json({
    success: true,
    is_active: newStatus,
  });
});

admin.post('/api/admin/users/:userId/toggle-admin', requireAdmin, async (c) => {
  const currentUser = c.get('user') as User;
  const userId = parseInt(c.req.param('userId'));

  const userRepo = new UserRepository(c.env.DB);
  const targetUser = await userRepo.findById(userId);

  if (!targetUser) {
    return c.json({ error: 'User not found' } as ApiResponse, 404);
  }

  if (targetUser.id === currentUser.id) {
    return c.json({ error: 'Cannot toggle your own admin status' } as ApiResponse, 400);
  }

  const newStatus = targetUser.is_admin !== 1;
  await userRepo.update(targetUser.id, { is_admin: newStatus ? 1 : 0 });

  return c.json({
    success: true,
    is_admin: newStatus,
  });
});

admin.post('/api/admin/media/:fileId/hard-delete', requireAdmin, async (c) => {
  const fileId = c.req.param('fileId');
  const body = await c.req.parseBody();
  const reason = (body.reason as string) || 'Admin hard delete';

  const mediaRepo = new MediaFileRepository(c.env.DB);
  const mediaFile = await mediaRepo.findByFileId(fileId);

  if (!mediaFile) {
    return c.json({ error: 'File not found' } as ApiResponse, 404);
  }

  const pathsToDelete: string[] = [];
  if (mediaFile.original_path) pathsToDelete.push(mediaFile.original_path);
  if (mediaFile.standard_path) pathsToDelete.push(mediaFile.standard_path);
  if (mediaFile.low_path) pathsToDelete.push(mediaFile.low_path);
  if (mediaFile.icon_path) pathsToDelete.push(mediaFile.icon_path);

  for (const path of pathsToDelete) {
    try {
      await c.env.MEDIA_BUCKET.delete(path);
    } catch (e) {
      console.error('Failed to delete R2 object:', e);
    }
  }

  await c.env.DB.prepare('DELETE FROM media_files WHERE id = ?').bind(mediaFile.id).run();

  return c.json({
    success: true,
    message: `File permanently deleted. ${pathsToDelete.length} physical files removed.`,
    deleted_files: pathsToDelete,
  });
});

admin.post('/api/admin/media/:fileId/restore', requireAdmin, async (c) => {
  const fileId = c.req.param('fileId');

  const mediaRepo = new MediaFileRepository(c.env.DB);
  const mediaFile = await mediaRepo.findByFileId(fileId);

  if (!mediaFile) {
    return c.json({ error: 'File not found' } as ApiResponse, 404);
  }

  if (mediaFile.is_deleted !== 1) {
    return c.json({ success: true, message: 'File is not deleted' });
  }

  await mediaRepo.update(mediaFile.id, {
    is_deleted: 0,
    deleted_at: null,
    deleted_reason: null,
  });

  return c.json({
    success: true,
    message: 'File has been restored by admin',
  });
});

admin.get('/admin/cleanup', requireAdmin, async (c) => {
  const user = c.get('user') as User;
  const mediaRepo = new MediaFileRepository(c.env.DB);

  const expiredCount = await mediaRepo.countExpired();
  const softDeletedCount = await mediaRepo.countDeleted();

  return c.html(await renderAdminCleanup(c, user, expiredCount, softDeletedCount));
});

admin.post('/api/admin/cleanup/expired', requireAdmin, async (c) => {
  const mediaRepo = new MediaFileRepository(c.env.DB);
  const count = await mediaRepo.softDeleteExpired();

  return c.json({
    success: true,
    message: `Soft deleted ${count} expired files`,
    count,
  });
});

admin.post('/api/admin/cleanup/permanent', requireAdmin, async (c) => {
  const body = await c.req.parseBody();
  const days = parseInt((body.days as string) || '90');
  
  const mediaRepo = new MediaFileRepository(c.env.DB);
  const count = await mediaRepo.hardDeleteOldDeleted(days);

  return c.json({
    success: true,
    message: `Permanently deleted ${count} files`,
    count,
  });
});

async function renderAdminDashboard(
  c: Context<{ Bindings: Env }>,
  user: User,
  data: {
    userCount: number;
    fileCount: number;
    deletedCount: number;
    expiredCount: number;
    users: User[];
    files: MediaFile[];
  }
): Promise<string> {
  const userRows = data.users.map((u) => `
    <tr class="border-b border-gray-200">
      <td class="px-4 py-3 text-sm">${u.username}</td>
      <td class="px-4 py-3 text-sm text-gray-500">${u.email}</td>
      <td class="px-4 py-3">
        <span class="px-2 py-1 text-xs rounded ${u.is_active === 1 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}">
          ${u.is_active === 1 ? '活跃' : '禁用'}
        </span>
      </td>
      <td class="px-4 py-3">
        <span class="px-2 py-1 text-xs rounded ${u.is_admin === 1 ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-700'}">
          ${u.is_admin === 1 ? '管理员' : '普通用户'}
        </span>
      </td>
      <td class="px-4 py-3 text-sm">
        <div class="flex gap-2">
          <button onclick="toggleActive(${u.id})" class="text-blue-600 hover:underline text-xs">切换状态</button>
          <button onclick="toggleAdmin(${u.id})" class="text-purple-600 hover:underline text-xs">切换管理员</button>
          <a href="/admin/users/${u.id}/files" class="text-green-600 hover:underline text-xs">查看文件</a>
        </div>
      </td>
    </tr>
  `).join('');

  const fileRows = data.files.map((f) => `
    <tr class="border-b border-gray-200">
      <td class="px-4 py-3 text-sm font-medium truncate max-w-xs" title="${f.original_filename}">${f.original_filename}</td>
      <td class="px-4 py-3 text-sm text-gray-500">${f.media_type}</td>
      <td class="px-4 py-3 text-sm text-gray-500">${(f.file_size / 1024).toFixed(1)} KB</td>
      <td class="px-4 py-3 text-sm">${f.view_count}</td>
      <td class="px-4 py-3">
        <div class="flex flex-wrap gap-1">
          ${f.is_deleted === 1 ? '<span class="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded">已删除</span>' : ''}
          ${f.is_expired === 1 ? '<span class="px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded">已过期</span>' : ''}
        </div>
      </td>
      <td class="px-4 py-3 text-sm">
        <div class="flex gap-2">
          <a href="${getFileUrl(c, f.file_id, 'original')}" target="_blank" class="text-blue-600 hover:underline text-xs">查看</a>
          ${f.is_deleted === 1 
            ? `<button onclick="restoreFile('${f.file_id}')" class="text-green-600 hover:underline text-xs">恢复</button>`
            : `<button onclick="hardDeleteFile('${f.file_id}')" class="text-red-600 hover:underline text-xs">永久删除</button>`
          }
        </div>
      </td>
    </tr>
  `).join('');

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>管理后台 - 图床服务</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen bg-gray-50">
  <nav class="bg-white shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16 items-center">
        <div class="flex items-center gap-8">
          <span class="text-xl font-bold text-purple-600">图床服务</span>
          <div class="flex gap-4">
            <a href="/dashboard" class="text-gray-600 hover:text-purple-600">仪表盘</a>
            <a href="/upload" class="text-gray-600 hover:text-purple-600">上传</a>
            <a href="/admin" class="text-purple-600 font-medium">管理</a>
            <a href="/admin/cleanup" class="text-gray-600 hover:text-purple-600">清理</a>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <span class="text-gray-600">${user.username}</span>
          <a href="/logout" class="text-red-600 hover:underline">退出</a>
        </div>
      </div>
    </div>
  </nav>
  
  <div class="max-w-7xl mx-auto py-8 px-4">
    <h1 class="text-3xl font-bold text-gray-800 mb-8">管理后台</h1>
    
    <div class="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="text-3xl font-bold text-purple-600">${data.userCount}</div>
        <div class="text-gray-500 mt-1">用户总数</div>
      </div>
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="text-3xl font-bold text-blue-600">${data.fileCount}</div>
        <div class="text-gray-500 mt-1">文件总数</div>
      </div>
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="text-3xl font-bold text-red-600">${data.deletedCount}</div>
        <div class="text-gray-500 mt-1">已删除文件</div>
      </div>
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="text-3xl font-bold text-yellow-600">${data.expiredCount}</div>
        <div class="text-gray-500 mt-1">已过期文件</div>
      </div>
    </div>
    
    <div class="bg-white rounded-xl shadow-sm p-6 mb-8">
      <h2 class="text-xl font-semibold text-gray-800 mb-4">用户管理</h2>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-200 text-left">
              <th class="px-4 py-3 text-sm font-medium text-gray-500">用户名</th>
              <th class="px-4 py-3 text-sm font-medium text-gray-500">邮箱</th>
              <th class="px-4 py-3 text-sm font-medium text-gray-500">状态</th>
              <th class="px-4 py-3 text-sm font-medium text-gray-500">角色</th>
              <th class="px-4 py-3 text-sm font-medium text-gray-500">操作</th>
            </tr>
          </thead>
          <tbody>
            ${userRows}
          </tbody>
        </table>
      </div>
    </div>
    
    <div class="bg-white rounded-xl shadow-sm p-6">
      <h2 class="text-xl font-semibold text-gray-800 mb-4">文件管理</h2>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-200 text-left">
              <th class="px-4 py-3 text-sm font-medium text-gray-500">文件名</th>
              <th class="px-4 py-3 text-sm font-medium text-gray-500">类型</th>
              <th class="px-4 py-3 text-sm font-medium text-gray-500">大小</th>
              <th class="px-4 py-3 text-sm font-medium text-gray-500">访问</th>
              <th class="px-4 py-3 text-sm font-medium text-gray-500">状态</th>
              <th class="px-4 py-3 text-sm font-medium text-gray-500">操作</th>
            </tr>
          </thead>
          <tbody>
            ${fileRows}
          </tbody>
        </table>
      </div>
    </div>
  </div>
  
  <script>
    async function toggleActive(userId) {
      const res = await fetch('/api/admin/users/' + userId + '/toggle-active', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        alert('状态已更新');
        location.reload();
      }
    }
    
    async function toggleAdmin(userId) {
      const res = await fetch('/api/admin/users/' + userId + '/toggle-admin', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        alert('管理员状态已更新');
        location.reload();
      }
    }
    
    async function hardDeleteFile(fileId) {
      if (!confirm('确定要永久删除此文件吗？此操作不可撤销。')) return;
      const formData = new FormData();
      formData.append('reason', 'Admin manual delete');
      const res = await fetch('/api/admin/media/' + fileId + '/hard-delete', { method: 'POST', body: formData });
      const data = await res.json();
      if (data.success) {
        alert(data.message);
        location.reload();
      }
    }
    
    async function restoreFile(fileId) {
      const res = await fetch('/api/admin/media/' + fileId + '/restore', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        alert(data.message);
        location.reload();
      }
    }
  </script>
</body>
</html>`;
}

async function renderAdminUserFiles(
  c: Context<{ Bindings: Env }>,
  user: User,
  targetUser: User,
  files: MediaFile[]
): Promise<string> {
  const fileItems = files.map((f) => `
    <div class="bg-white rounded-lg shadow-sm p-4 border border-gray-100">
      <div class="flex items-start justify-between">
        <div class="flex-1">
          <h3 class="font-medium text-gray-800 truncate" title="${f.original_filename}">${f.original_filename}</h3>
          <div class="mt-1 text-sm text-gray-500 space-x-4">
            <span>${(f.file_size / 1024).toFixed(1)} KB</span>
            <span>${f.media_type}</span>
            <span>访问: ${f.view_count}</span>
          </div>
        </div>
        <div class="flex items-center gap-2 ml-4">
          ${f.is_deleted === 1 ? '<span class="px-2 py-1 bg-red-100 text-red-700 text-xs rounded">已删除</span>' : ''}
          ${f.is_expired === 1 ? '<span class="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded">已过期</span>' : ''}
        </div>
      </div>
      <div class="mt-3 flex flex-wrap gap-2">
        <a href="${getFileUrl(c, f.file_id, 'original')}" target="_blank" class="px-3 py-1 bg-purple-100 text-purple-700 text-sm rounded hover:bg-purple-200">查看</a>
        ${f.is_deleted === 1 
          ? `<button onclick="restoreFile('${f.file_id}')" class="px-3 py-1 bg-green-100 text-green-700 text-sm rounded hover:bg-green-200">恢复</button>`
          : `<button onclick="hardDeleteFile('${f.file_id}')" class="px-3 py-1 bg-red-100 text-red-700 text-sm rounded hover:bg-red-200">永久删除</button>`
        }
      </div>
    </div>
  `).join('');

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>用户文件 - 图床服务</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen bg-gray-50">
  <nav class="bg-white shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16 items-center">
        <div class="flex items-center gap-8">
          <span class="text-xl font-bold text-purple-600">图床服务</span>
          <div class="flex gap-4">
            <a href="/dashboard" class="text-gray-600 hover:text-purple-600">仪表盘</a>
            <a href="/admin" class="text-purple-600 font-medium">管理</a>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <span class="text-gray-600">${user.username}</span>
          <a href="/logout" class="text-red-600 hover:underline">退出</a>
        </div>
      </div>
    </div>
  </nav>
  
  <div class="max-w-7xl mx-auto py-8 px-4">
    <div class="mb-8">
      <a href="/admin" class="text-purple-600 hover:underline mb-2 inline-block">← 返回管理后台</a>
      <h1 class="text-3xl font-bold text-gray-800">用户文件: ${targetUser.username}</h1>
      <p class="text-gray-500 mt-1">${targetUser.email}</p>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="text-3xl font-bold text-purple-600">${files.length}</div>
        <div class="text-gray-500 mt-1">文件总数</div>
      </div>
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="text-3xl font-bold text-blue-600">${files.reduce((s, f) => s + f.view_count, 0)}</div>
        <div class="text-gray-500 mt-1">总访问量</div>
      </div>
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="text-3xl font-bold text-red-600">${files.filter((f) => f.is_deleted === 1).length}</div>
        <div class="text-gray-500 mt-1">已删除文件</div>
      </div>
    </div>
    
    ${files.length === 0 
      ? '<div class="bg-white rounded-xl shadow-sm p-12 text-center"><p class="text-gray-500">该用户没有上传任何文件</p></div>'
      : `<div class="space-y-4">${fileItems}</div>`
    }
  </div>
  
  <script>
    async function hardDeleteFile(fileId) {
      if (!confirm('确定要永久删除此文件吗？此操作不可撤销。')) return;
      const formData = new FormData();
      formData.append('reason', 'Admin manual delete');
      const res = await fetch('/api/admin/media/' + fileId + '/hard-delete', { method: 'POST', body: formData });
      const data = await res.json();
      if (data.success) {
        alert(data.message);
        location.reload();
      }
    }
    
    async function restoreFile(fileId) {
      const res = await fetch('/api/admin/media/' + fileId + '/restore', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        alert(data.message);
        location.reload();
      }
    }
  </script>
</body>
</html>`;
}

async function renderAdminCleanup(
  c: Context<{ Bindings: Env }>,
  user: User,
  expiredCount: number,
  softDeletedCount: number
): Promise<string> {
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>系统清理 - 图床服务</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen bg-gray-50">
  <nav class="bg-white shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16 items-center">
        <div class="flex items-center gap-8">
          <span class="text-xl font-bold text-purple-600">图床服务</span>
          <div class="flex gap-4">
            <a href="/dashboard" class="text-gray-600 hover:text-purple-600">仪表盘</a>
            <a href="/admin" class="text-gray-600 hover:text-purple-600">管理</a>
            <a href="/admin/cleanup" class="text-purple-600 font-medium">清理</a>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <span class="text-gray-600">${user.username}</span>
          <a href="/logout" class="text-red-600 hover:underline">退出</a>
        </div>
      </div>
    </div>
  </nav>
  
  <div class="max-w-4xl mx-auto py-8 px-4">
    <h1 class="text-3xl font-bold text-gray-800 mb-8">系统清理</h1>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="text-3xl font-bold text-yellow-600">${expiredCount}</div>
        <div class="text-gray-500 mt-1">已过期文件</div>
      </div>
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="text-3xl font-bold text-red-600">${softDeletedCount}</div>
        <div class="text-gray-500 mt-1">已软删除文件</div>
      </div>
    </div>
    
    <div class="space-y-6">
      <div class="bg-white rounded-xl shadow-sm p-6">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">清理过期文件</h2>
        <p class="text-gray-500 mb-4">将所有已过期的文件标记为已删除（软删除）。</p>
        <button onclick="cleanupExpired()" 
          class="px-6 py-3 bg-yellow-600 text-white rounded-lg font-medium hover:bg-yellow-700 transition-all">
          清理过期文件 (${expiredCount} 个)
        </button>
      </div>
      
      <div class="bg-white rounded-xl shadow-sm p-6">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">永久删除已软删除文件</h2>
        <p class="text-gray-500 mb-4">永久删除指定天数前已软删除的文件。此操作不可撤销！</p>
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2">
            <label class="text-sm text-gray-600">删除</label>
            <select id="deleteDays" class="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500">
              <option value="7">7 天前</option>
              <option value="30">30 天前</option>
              <option value="90" selected>90 天前</option>
              <option value="180">180 天前</option>
            </select>
            <label class="text-sm text-gray-600">的已删除文件</label>
          </div>
          <button onclick="cleanupPermanent()" 
            class="px-6 py-3 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-all">
            永久删除 (${softDeletedCount} 个)
          </button>
        </div>
      </div>
    </div>
  </div>
  
  <script>
    async function cleanupExpired() {
      if (!confirm('确定要清理所有已过期的文件吗？这些文件将被软删除。')) return;
      const res = await fetch('/api/admin/cleanup/expired', { method: 'POST' });
      const data = await res.json();
      alert(data.message);
      location.reload();
    }
    
    async function cleanupPermanent() {
      const days = document.getElementById('deleteDays').value;
      if (!confirm(\`确定要永久删除 \${days} 天前的所有已软删除文件吗？此操作不可撤销！\`)) return;
      
      const formData = new FormData();
      formData.append('days', days);
      
      const res = await fetch('/api/admin/cleanup/permanent', { method: 'POST', body: formData });
      const data = await res.json();
      alert(data.message);
      location.reload();
    }
  </script>
</body>
</html>`;
}

import type { Context } from 'hono';

export { admin };
