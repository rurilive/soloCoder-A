import { Hono } from 'hono';
import type { Env, User, MediaFile, MediaType, QualityLevel, ApiResponse, MediaFileResponse, UploadResponse } from '../types';
import { MediaFileRepository, UserRepository } from '../repositories';
import { requireAuth, getCurrentUser } from '../middleware/auth';
import { generateFileId, hashFilename, QUALITY_CONFIGS, parseAllowedTypes } from '../utils/security';

const media = new Hono<{ Bindings: Env }>();

function getFileUrl(c: Context<{ Bindings: Env }>, fileId: string, quality: string): string {
  const url = new URL(c.req.url);
  return `${url.origin}/file/${fileId}/${quality}`;
}

function buildMediaFileResponse(
  c: Context<{ Bindings: Env }>,
  file: MediaFile,
  includeToken: boolean = false,
  userToken?: string
): MediaFileResponse {
  const response: MediaFileResponse = {
    id: file.id,
    file_id: file.file_id,
    original_filename: file.original_filename,
    media_type: file.media_type,
    mime_type: file.mime_type,
    file_size: file.file_size,
    width: file.width,
    height: file.height,
    view_count: file.view_count,
    created_at: file.created_at,
    updated_at: file.updated_at,
    expires_at: file.expires_at,
    is_expired: file.is_expired === 1,
    is_deleted: file.is_deleted === 1,
    deleted_at: file.deleted_at,
    original_url: getFileUrl(c, file.file_id, 'original'),
    standard_url: file.standard_path ? getFileUrl(c, file.file_id, 'standard') : undefined,
    low_url: file.low_path ? getFileUrl(c, file.file_id, 'low') : undefined,
    icon_url: file.icon_path ? getFileUrl(c, file.file_id, 'icon') : undefined,
  };

  if (includeToken && userToken && file.require_token === 1) {
    const addToken = (url: string) => {
      const separator = url.includes('?') ? '&' : '?';
      return `${url}${separator}st=${userToken}`;
    };
    response.original_url = addToken(response.original_url);
    if (response.standard_url) response.standard_url = addToken(response.standard_url);
    if (response.low_url) response.low_url = addToken(response.low_url);
    if (response.icon_url) response.icon_url = addToken(response.icon_url);
  }

  return response;
}

media.get('/upload', requireAuth, async (c) => {
  const user = c.get('user') as User;
  return c.html(await renderUploadPage(c, user));
});

media.post('/upload', requireAuth, async (c) => {
  const user = c.get('user') as User;
  const body = await c.req.parseBody();
  const file = body.file as File | undefined;
  
  if (!file || !file.name) {
    return c.json({ success: false, message: 'No file selected' } as UploadResponse, 400);
  }

  const allowedImageTypes = parseAllowedTypes(c.env.ALLOWED_IMAGE_TYPES);
  const allowedVideoTypes = parseAllowedTypes(c.env.ALLOWED_VIDEO_TYPES);
  const allowedTypes = [...allowedImageTypes, ...allowedVideoTypes];

  const mimeType = file.type || 'application/octet-stream';
  let mediaType: MediaType;
  
  if (allowedImageTypes.includes(mimeType)) {
    mediaType = 'image';
  } else if (allowedVideoTypes.includes(mimeType)) {
    mediaType = 'video';
  } else {
    return c.json({ success: false, message: `File type ${mimeType} not allowed` } as UploadResponse, 400);
  }

  const maxFileSize = parseInt(c.env.MAX_FILE_SIZE as unknown as string) || 104857600;
  if (file.size > maxFileSize) {
    return c.json({ success: false, message: `File too large. Maximum size is ${maxFileSize} bytes` } as UploadResponse, 413);
  }

  const expireDays = parseInt((body.expire_days as string) || '0');
  const requireToken = (body.require_token as string) === 'on' || body.require_token === true;
  const allowedReferers = (body.allowed_referers as string) || '';

  const fileId = generateFileId();
  const baseFilename = hashFilename(file.name);
  const ext = '.' + (file.name.split('.').pop()?.toLowerCase() || 'jpg');

  const uuidParts = user.uuid.split('-').slice(0, 2).join('/');
  const storagePrefix = `${uuidParts}/${baseFilename}`;

  const fileBuffer = await file.arrayBuffer();
  const expiresAt = expireDays > 0 
    ? new Date(Date.now() + expireDays * 24 * 60 * 60 * 1000).toISOString()
    : null;

  let width: number | undefined;
  let height: number | undefined;
  const originalPath = `${storagePrefix}_original${ext}`;

  await c.env.MEDIA_BUCKET.put(originalPath, fileBuffer, {
    httpMetadata: { contentType: mimeType },
    customMetadata: {
      fileId,
      userId: String(user.id),
      originalFilename: file.name,
    },
  });

  const mediaRepo = new MediaFileRepository(c.env.DB);
  
  const mediaFile = await mediaRepo.create({
    file_id: fileId,
    user_id: user.id,
    original_filename: file.name,
    media_type: mediaType,
    mime_type: mimeType,
    file_size: file.size,
    width,
    height,
    original_path: originalPath,
    standard_path: null,
    low_path: null,
    icon_path: null,
    original_size: file.size,
    standard_size: null,
    low_size: null,
    icon_size: null,
    telegram_file_id: null,
    telegram_message_id: null,
    is_public: 1,
    expires_at: expiresAt,
    require_token: requireToken ? 1 : 0,
    allowed_referers: allowedReferers.trim() || null,
  });

  const response: UploadResponse = {
    success: true,
    message: 'File uploaded successfully',
    file: buildMediaFileResponse(c, mediaFile),
  };

  return c.json(response);
});

media.get('/file/:fileId/:quality', async (c) => {
  const fileId = c.req.param('fileId');
  const quality = c.req.param('quality') as QualityLevel;
  const st = c.req.query('st');

  if (!['original', 'standard', 'low', 'icon'].includes(quality)) {
    return c.json({ error: 'Invalid quality level' } as ApiResponse, 400);
  }

  const mediaRepo = new MediaFileRepository(c.env.DB);
  const mediaFile = await mediaRepo.findByFileId(fileId);

  if (!mediaFile) {
    return c.json({ error: 'File not found' } as ApiResponse, 404);
  }

  if (mediaFile.is_deleted === 1) {
    return c.json({ error: 'File not found' } as ApiResponse, 404);
  }

  const now = new Date();
  if (mediaFile.is_expired === 0 && mediaFile.expires_at) {
    if (now > new Date(mediaFile.expires_at)) {
      await mediaRepo.update(mediaFile.id, { is_expired: 1 });
      mediaFile.is_expired = 1;
    }
  }

  if (mediaFile.is_expired === 1) {
    return c.json({ error: 'File has expired' } as ApiResponse, 410);
  }

  if (mediaFile.is_public !== 1) {
    return c.json({ error: 'File is not public' } as ApiResponse, 403);
  }

  if (mediaFile.require_token === 1) {
    const referer = c.req.header('Referer');
    let tokenValid = false;
    let refererValid = false;

    if (st) {
      const userRepo = new UserRepository(c.env.DB);
      const owner = await userRepo.findById(mediaFile.user_id);
      if (owner && st === owner.secret_token) {
        tokenValid = true;
      }
    }

    if (!tokenValid && mediaFile.allowed_referers) {
      refererValid = isRefererAllowed(referer, mediaFile.allowed_referers);
    }

    if (!tokenValid && !refererValid) {
      return c.json({ error: 'Access denied. Valid token or referer required.' } as ApiResponse, 403);
    }
  }

  const pathAttr = `${quality}_path` as keyof MediaFile;
  let filePath = mediaFile[pathAttr] as string | null;

  if (!filePath) {
    if (quality === 'original') {
      return c.json({ error: 'File not found' } as ApiResponse, 404);
    }
    filePath = mediaFile.original_path;
  }

  const object = await c.env.MEDIA_BUCKET.get(filePath);
  if (!object) {
    return c.json({ error: 'File not found' } as ApiResponse, 404);
  }

  await mediaRepo.incrementViewCount(mediaFile.id);

  const headers = new Headers();
  object.writeHttpMetadata(headers);
  headers.set('Cache-Control', 'public, max-age=31536000');
  headers.set('Content-Disposition', `inline; filename="${encodeURIComponent(mediaFile.original_filename)}"`);

  return new Response(object.body, { headers });
});

function isRefererAllowed(referer: string | null, allowedReferers: string): boolean {
  if (!allowedReferers || allowedReferers.trim() === '') return false;
  if (!referer) return false;

  const allowedList = allowedReferers.split(',').map((r) => r.trim()).filter(Boolean);
  return allowedList.some((allowed) => referer.includes(allowed));
}

media.get('/dashboard', requireAuth, async (c) => {
  const user = c.get('user') as User;
  const mediaRepo = new MediaFileRepository(c.env.DB);
  
  const files = await mediaRepo.findByUserId(user.id, 50, 0);
  
  const now = new Date();
  for (const file of files) {
    if (file.is_expired === 0 && file.expires_at) {
      if (now > new Date(file.expires_at)) {
        await mediaRepo.update(file.id, { is_expired: 1 });
        file.is_expired = 1;
      }
    }
  }

  return c.html(await renderDashboardPage(c, user, files));
});

media.put('/api/media/:fileId/expire', requireAuth, async (c) => {
  const user = c.get('user') as User;
  const fileId = c.req.param('fileId');
  const body = await c.req.parseBody();
  const expireDays = parseInt((body.expire_days as string) || '0');

  const mediaRepo = new MediaFileRepository(c.env.DB);
  const mediaFile = await mediaRepo.findByFileId(fileId);

  if (!mediaFile || mediaFile.user_id !== user.id) {
    return c.json({ error: 'File not found' } as ApiResponse, 404);
  }

  if (mediaFile.is_deleted === 1) {
    return c.json({ error: 'File has been deleted' } as ApiResponse, 400);
  }

  const expiresAt = expireDays > 0
    ? new Date(Date.now() + expireDays * 24 * 60 * 60 * 1000).toISOString()
    : null;

  await mediaRepo.update(mediaFile.id, {
    expires_at: expiresAt,
    is_expired: 0,
  });

  return c.json({
    success: true,
    message: 'Expire time updated',
    expires_at: expiresAt,
    is_expired: false,
  });
});

media.post('/api/media/:fileId/soft-delete', requireAuth, async (c) => {
  const user = c.get('user') as User;
  const fileId = c.req.param('fileId');
  const body = await c.req.parseBody();
  const reason = (body.reason as string) || '';

  const mediaRepo = new MediaFileRepository(c.env.DB);
  const mediaFile = await mediaRepo.findByFileId(fileId);

  if (!mediaFile || mediaFile.user_id !== user.id) {
    return c.json({ error: 'File not found' } as ApiResponse, 404);
  }

  if (mediaFile.is_deleted === 1) {
    return c.json({ success: true, message: 'File is already deleted' });
  }

  await mediaRepo.update(mediaFile.id, {
    is_deleted: 1,
    deleted_at: new Date().toISOString(),
    deleted_reason: reason || null,
  });

  return c.json({
    success: true,
    message: 'File has been soft deleted',
    deleted_at: new Date().toISOString(),
  });
});

media.post('/api/media/:fileId/restore', requireAuth, async (c) => {
  const user = c.get('user') as User;
  const fileId = c.req.param('fileId');

  const mediaRepo = new MediaFileRepository(c.env.DB);
  const mediaFile = await mediaRepo.findByFileId(fileId);

  if (!mediaFile || mediaFile.user_id !== user.id) {
    return c.json({ error: 'File not found' } as ApiResponse, 404);
  }

  if (mediaFile.is_deleted !== 1) {
    return c.json({ success: true, message: 'File is not deleted' });
  }

  await mediaRepo.update(mediaFile.id, {
    is_deleted: 0,
  });

  return c.json({
    success: true,
    message: 'File has been restored',
  });
});

media.get('/api/user/token', requireAuth, async (c) => {
  const user = c.get('user') as User;
  return c.json({
    success: true,
    token: user.secret_token,
  });
});

media.post('/api/user/token/reset', requireAuth, async (c) => {
  const user = c.get('user') as User;
  const userRepo = new UserRepository(c.env.DB);
  const newToken = generateFileId() + generateFileId();

  await userRepo.update(user.id, { secret_token: newToken });

  return c.json({
    success: true,
    message: 'Token has been reset',
    token: newToken,
  });
});

media.put('/api/media/:fileId/token-settings', requireAuth, async (c) => {
  const user = c.get('user') as User;
  const fileId = c.req.param('fileId');
  const body = await c.req.parseBody();
  const requireToken = (body.require_token as string) === 'on' || body.require_token === true;
  const allowedReferers = (body.allowed_referers as string) || '';

  const mediaRepo = new MediaFileRepository(c.env.DB);
  const mediaFile = await mediaRepo.findByFileId(fileId);

  if (!mediaFile || mediaFile.user_id !== user.id) {
    return c.json({ error: 'File not found' } as ApiResponse, 404);
  }

  await mediaRepo.update(mediaFile.id, {
    require_token: requireToken ? 1 : 0,
    allowed_referers: allowedReferers.trim() || null,
  });

  return c.json({
    success: true,
    message: 'Token settings updated',
    require_token: requireToken,
    allowed_referers: allowedReferers.trim() || null,
  });
});

async function renderUploadPage(c: Context<{ Bindings: Env }>, user: User): Promise<string> {
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>上传文件 - 图床服务</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen bg-gray-50">
  <nav class="bg-white shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16 items-center">
        <a href="/dashboard" class="text-xl font-bold text-purple-600">图床服务</a>
        <div class="flex items-center gap-4">
          <span class="text-gray-600">${user.username}</span>
          <a href="/logout" class="text-red-600 hover:underline">退出</a>
        </div>
      </div>
    </div>
  </nav>
  
  <div class="max-w-4xl mx-auto py-12 px-4">
    <h1 class="text-3xl font-bold text-gray-800 mb-8">上传文件</h1>
    
    <form id="uploadForm" class="space-y-6 bg-white p-8 rounded-xl shadow-sm">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">选择文件</label>
        <input type="file" name="file" id="fileInput" required
          class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500">
        <p class="mt-1 text-sm text-gray-500">支持图片（JPG, PNG, GIF, WebP）和视频（MP4, WebM, QuickTime），最大100MB</p>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">过期天数（0=永不过期）</label>
          <input type="number" name="expire_days" value="0" min="0"
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500">
        </div>
        
        <div class="flex items-center">
          <input type="checkbox" name="require_token" id="requireToken"
            class="w-4 h-4 text-purple-600 rounded">
          <label for="requireToken" class="ml-2 text-sm text-gray-700">需要访问令牌</label>
        </div>
      </div>
      
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">允许的引用域名（逗号分隔，可选）</label>
        <input type="text" name="allowed_referers" placeholder="example.com, another-domain.com"
          class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500">
      </div>
      
      <button type="submit"
        class="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-blue-700 transition-all">
        上传文件
      </button>
    </form>
    
    <div id="result" class="mt-8 hidden"></div>
  </div>
  
  <script>
    document.getElementById('uploadForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(e.target);
      const resultDiv = document.getElementById('result');
      
      try {
        const res = await fetch('/upload', { method: 'POST', body: formData });
        const data = await res.json();
        
        if (data.success && data.file) {
          resultDiv.className = 'mt-8 p-6 bg-green-50 rounded-xl';
          resultDiv.innerHTML = \`
            <h3 class="text-lg font-semibold text-green-800 mb-4">上传成功！</h3>
            <div class="space-y-2">
              <p><span class="font-medium">原始链接：</span><a href="\${data.file.original_url}" target="_blank" class="text-purple-600 hover:underline">\${data.file.original_url}</a></p>
              \${data.file.standard_url ? \`<p><span class="font-medium">标准链接：</span><a href="\${data.file.standard_url}" target="_blank" class="text-purple-600 hover:underline">\${data.file.standard_url}</a></p>\` : ''}
              \${data.file.low_url ? \`<p><span class="font-medium">低清链接：</span><a href="\${data.file.low_url}" target="_blank" class="text-purple-600 hover:underline">\${data.file.low_url}</a></p>\` : ''}
            </div>
            <a href="/dashboard" class="mt-4 inline-block text-purple-600 hover:underline">返回仪表盘</a>
          \`;
        } else {
          resultDiv.className = 'mt-8 p-6 bg-red-50 rounded-xl';
          resultDiv.innerHTML = \`<p class="text-red-700">上传失败：\${data.message || '未知错误'}</p>\`;
        }
      } catch (err) {
        resultDiv.className = 'mt-8 p-6 bg-red-50 rounded-xl';
        resultDiv.innerHTML = '<p class="text-red-700">网络错误</p>';
      }
    });
  </script>
</body>
</html>`;
}

async function renderDashboardPage(c: Context<{ Bindings: Env }>, user: User, files: MediaFile[]): Promise<string> {
  const fileItems = files.map((f) => {
    const originalUrl = getFileUrl(c, f.file_id, 'original');
    const standardUrl = f.standard_path ? getFileUrl(c, f.file_id, 'standard') : null;
    const lowUrl = f.low_path ? getFileUrl(c, f.file_id, 'low') : null;
    const iconUrl = f.icon_path ? getFileUrl(c, f.file_id, 'icon') : null;

    return `
      <div class="bg-white rounded-lg shadow-sm p-4 border border-gray-100">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <h3 class="font-medium text-gray-800 truncate" title="${f.original_filename}">${f.original_filename}</h3>
            <div class="mt-1 text-sm text-gray-500 space-x-4">
              <span>${(f.file_size / 1024).toFixed(1)} KB</span>
              <span>${f.media_type}</span>
              <span>访问: ${f.view_count}</span>
              ${f.expires_at ? `<span class="${f.is_expired === 1 ? 'text-red-500' : ''}">${f.is_expired === 1 ? '已过期' : '过期: ' + new Date(f.expires_at).toLocaleDateString()}</span>` : ''}
            </div>
          </div>
          <div class="flex items-center gap-2 ml-4">
            ${f.is_deleted === 1 ? '<span class="px-2 py-1 bg-red-100 text-red-700 text-xs rounded">已删除</span>' : ''}
            ${f.is_expired === 1 ? '<span class="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded">已过期</span>' : ''}
            ${f.require_token === 1 ? '<span class="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">需令牌</span>' : ''}
          </div>
        </div>
        <div class="mt-3 flex flex-wrap gap-2">
          <a href="${originalUrl}" target="_blank" class="px-3 py-1 bg-purple-100 text-purple-700 text-sm rounded hover:bg-purple-200">原图</a>
          ${standardUrl ? `<a href="${standardUrl}" target="_blank" class="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded hover:bg-gray-200">标准</a>` : ''}
          ${lowUrl ? `<a href="${lowUrl}" target="_blank" class="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded hover:bg-gray-200">低清</a>` : ''}
        </div>
      </div>
    `;
  }).join('');

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>仪表盘 - 图床服务</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen bg-gray-50">
  <nav class="bg-white shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16 items-center">
        <div class="flex items-center gap-8">
          <span class="text-xl font-bold text-purple-600">图床服务</span>
          <div class="flex gap-4">
            <a href="/dashboard" class="text-purple-600 font-medium">仪表盘</a>
            <a href="/upload" class="text-gray-600 hover:text-purple-600">上传</a>
            ${user.is_admin === 1 ? '<a href="/admin" class="text-gray-600 hover:text-purple-600">管理</a>' : ''}
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
    <div class="flex justify-between items-center mb-8">
      <h1 class="text-3xl font-bold text-gray-800">仪表盘</h1>
      <a href="/upload" class="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:from-purple-700 hover:to-blue-700 transition-all">
        上传新文件
      </a>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="text-3xl font-bold text-purple-600">${files.length}</div>
        <div class="text-gray-500 mt-1">文件总数</div>
      </div>
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="text-3xl font-bold text-blue-600">${files.reduce((sum, f) => sum + f.view_count, 0)}</div>
        <div class="text-gray-500 mt-1">总访问量</div>
      </div>
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="text-3xl font-bold text-green-600">${files.filter((f) => f.is_expired === 0).length}</div>
        <div class="text-gray-500 mt-1">有效文件</div>
      </div>
    </div>
    
    <div class="bg-white rounded-xl shadow-sm p-6 mb-8">
      <h2 class="text-lg font-semibold text-gray-800 mb-4">您的访问令牌</h2>
      <div class="flex items-center gap-4">
        <code class="flex-1 bg-gray-100 px-4 py-2 rounded font-mono text-sm">${user.secret_token}</code>
        <button onclick="copyToken()" class="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-all">复制</button>
      </div>
      <p class="mt-2 text-sm text-gray-500">此令牌用于访问标记为"需要令牌"的文件，URL格式：/file/{file_id}/original?st={token}</p>
    </div>
    
    <div class="mb-4">
      <h2 class="text-xl font-semibold text-gray-800">最近上传的文件</h2>
    </div>
    
    ${files.length === 0 
      ? '<div class="bg-white rounded-xl shadow-sm p-12 text-center"><p class="text-gray-500">还没有上传任何文件</p><a href="/upload" class="mt-4 inline-block text-purple-600 hover:underline">立即上传</a></div>'
      : `<div class="space-y-4">${fileItems}</div>`
    }
  </div>
  
  <script>
    async function copyToken() {
      const token = \`${user.secret_token}\`;
      await navigator.clipboard.writeText(token);
      alert('令牌已复制到剪贴板');
    }
  </script>
</body>
</html>`;
}

import type { Context } from 'hono';

export { media };
