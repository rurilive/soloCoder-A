import type { Env, TelegramUpdate, TelegramMessage, User, MediaType } from '../types';
import { UserRepository, MediaFileRepository } from '../repositories';
import { generateUUID, generateSecretToken, generateFileId, hashFilename, hashPassword } from '../utils/security';

export class TelegramService {
  private token: string;
  private channelId: string;
  private apiBase: string;

  constructor(env: Env) {
    this.token = env.TELEGRAM_BOT_TOKEN;
    this.channelId = env.TELEGRAM_CHANNEL_ID;
    this.apiBase = `https://api.telegram.org/bot${this.token}`;
  }

  async getMe(): Promise<unknown> {
    const response = await fetch(`${this.apiBase}/getMe`);
    return response.json();
  }

  async sendMessage(chatId: number | string, text: string, replyMarkup?: unknown): Promise<unknown> {
    const response = await fetch(`${this.apiBase}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: chatId,
        text,
        parse_mode: 'Markdown',
        reply_markup: replyMarkup,
      }),
    });
    return response.json();
  }

  async sendPhoto(
    chatId: number | string,
    photo: File | string,
    caption?: string
  ): Promise<{ messageId: number; fileId: string }> {
    const formData = new FormData();
    formData.append('chat_id', String(chatId));
    if (caption) formData.append('caption', caption);

    if (typeof photo === 'string') {
      formData.append('photo', photo);
    } else {
      formData.append('photo', photo);
    }

    const response = await fetch(`${this.apiBase}/sendPhoto`, {
      method: 'POST',
      body: formData,
    });

    const data = await response.json() as {
      ok: boolean;
      result?: {
        message_id: number;
        photo?: Array<{ file_id: string }>;
      };
    };

    if (!data.ok || !data.result) {
      throw new Error('Failed to send photo to Telegram');
    }

    const photos = data.result.photo || [];
    const largestPhoto = photos[photos.length - 1];

    return {
      messageId: data.result.message_id,
      fileId: largestPhoto?.file_id || '',
    };
  }

  async sendDocument(
    chatId: number | string,
    document: File | string,
    caption?: string
  ): Promise<{ messageId: number; fileId: string }> {
    const formData = new FormData();
    formData.append('chat_id', String(chatId));
    if (caption) formData.append('caption', caption);

    if (typeof document === 'string') {
      formData.append('document', document);
    } else {
      formData.append('document', document);
    }

    const response = await fetch(`${this.apiBase}/sendDocument`, {
      method: 'POST',
      body: formData,
    });

    const data = await response.json() as {
      ok: boolean;
      result?: {
        message_id: number;
        document?: { file_id: string };
      };
    };

    if (!data.ok || !data.result) {
      throw new Error('Failed to send document to Telegram');
    }

    return {
      messageId: data.result.message_id,
      fileId: data.result.document?.file_id || '',
    };
  }

  async sendVideo(
    chatId: number | string,
    video: File | string,
    caption?: string
  ): Promise<{ messageId: number; fileId: string }> {
    const formData = new FormData();
    formData.append('chat_id', String(chatId));
    if (caption) formData.append('caption', caption);

    if (typeof video === 'string') {
      formData.append('video', video);
    } else {
      formData.append('video', video);
    }

    const response = await fetch(`${this.apiBase}/sendVideo`, {
      method: 'POST',
      body: formData,
    });

    const data = await response.json() as {
      ok: boolean;
      result?: {
        message_id: number;
        video?: { file_id: string };
      };
    };

    if (!data.ok || !data.result) {
      throw new Error('Failed to send video to Telegram');
    }

    return {
      messageId: data.result.message_id,
      fileId: data.result.video?.file_id || '',
    };
  }

  async getFile(fileId: string): Promise<{ filePath: string }> {
    const response = await fetch(`${this.apiBase}/getFile?file_id=${fileId}`);
    const data = await response.json() as {
      ok: boolean;
      result?: { file_path: string };
    };

    if (!data.ok || !data.result?.file_path) {
      throw new Error('Failed to get file from Telegram');
    }

    return { filePath: data.result.file_path };
  }

  async getFileUrl(fileId: string): Promise<string> {
    const { filePath } = await this.getFile(fileId);
    return `https://api.telegram.org/file/bot${this.token}/${filePath}`;
  }

  async setWebhook(url: string, secretToken: string): Promise<unknown> {
    const response = await fetch(`${this.apiBase}/setWebhook`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url,
        secret_token: secretToken,
        allowed_updates: ['message', 'callback_query'],
      }),
    });
    return response.json();
  }

  async deleteWebhook(): Promise<unknown> {
    const response = await fetch(`${this.apiBase}/deleteWebhook`);
    return response.json();
  }
}

export class TelegramBotHandler {
  private env: Env;
  private service: TelegramService;

  constructor(env: Env) {
    this.env = env;
    this.service = new TelegramService(env);
  }

  async handleUpdate(update: TelegramUpdate): Promise<void> {
    if (update.message) {
      await this.handleMessage(update.message);
    } else if (update.callback_query) {
      await this.handleCallbackQuery(update.callback_query);
    }
  }

  private async handleMessage(message: TelegramMessage): Promise<void> {
    const chatId = message.chat.id;
    const userId = message.from.id;
    const text = message.text || '';

    const userRepo = new UserRepository(this.env.DB);
    let user = await userRepo.findByTelegramId(userId);

    if (!user) {
      const username = message.from.username || `user_${userId}`;
      const email = `${userId}@telegram.local`;
      
      user = await userRepo.create({
        uuid: generateUUID(),
        username,
        email,
        password_hash: await hashPassword(generateSecretToken()),
        secret_token: generateSecretToken(),
        is_active: 1,
        is_admin: 0,
        telegram_user_id: userId,
      });

      await this.service.sendMessage(
        chatId,
        `欢迎使用图床服务！\\n\\n您的账号已自动创建：\\n- 用户名: \`${username}\`\\n- 令牌: \`${user.secret_token}\`\\n\\n直接发送图片或文件即可上传。`
      );
      return;
    }

    if (text === '/start' || text === '/help') {
      await this.showHelp(chatId, user);
      return;
    }

    if (text === '/token') {
      await this.service.sendMessage(
        chatId,
        `您的访问令牌：\\n\`${user.secret_token}\`\\n\\n此令牌用于访问标记为"需要令牌"的文件。`
      );
      return;
    }

    if (text === '/files') {
      await this.showUserFiles(chatId, user);
      return;
    }

    if (text === '/stats') {
      await this.showStats(chatId, user);
      return;
    }

    if (message.photo && message.photo.length > 0) {
      await this.handlePhotoUpload(chatId, user, message);
      return;
    }

    if (message.document) {
      await this.handleDocumentUpload(chatId, user, message);
      return;
    }

    if (message.video) {
      await this.handleVideoUpload(chatId, user, message);
      return;
    }

    await this.service.sendMessage(
      chatId,
      '请发送图片或文件进行上传，或使用 /help 查看帮助。'
    );
  }

  private async handleCallbackQuery(callbackQuery: { id: string; data?: string; from: { id: number } }): Promise<void> {
    const data = callbackQuery.data || '';
    
    if (data.startsWith('file:')) {
      const fileId = data.replace('file:', '');
      const userRepo = new UserRepository(this.env.DB);
      const user = await userRepo.findByTelegramId(callbackQuery.from.id);
      
      if (user) {
        const mediaRepo = new MediaFileRepository(this.env.DB);
        const file = await mediaRepo.findByFileId(fileId);
        
        if (file && file.user_id === user.id) {
          const baseUrl = this.env.ENVIRONMENT === 'production' 
            ? `https://${new URL(this.env.TELEGRAM_WEBHOOK_SECRET || '').host || 'example.com'}`
            : 'http://localhost:8787';
          
          const urls = [
            `原图: ${baseUrl}/file/${fileId}/original`,
            file.standard_path ? `标准: ${baseUrl}/file/${fileId}/standard` : null,
            file.low_path ? `低清: ${baseUrl}/file/${fileId}/low` : null,
          ].filter(Boolean).join('\\n');
          
          await this.service.sendMessage(
            callbackQuery.from.id,
            `文件: \`${file.original_filename}\`\\n\\n访问链接:\\n${urls}`
          );
        }
      }
    }

    await fetch(`${this.service.apiBase}/answerCallbackQuery`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ callback_query_id: callbackQuery.id }),
    });
  }

  private async showHelp(chatId: number, user: User): Promise<void> {
    const helpText = `图床服务帮助\\n\\n` +
      `📤 *上传文件*\\n直接发送图片、视频或文档即可上传。\\n\\n` +
      `📋 *可用命令*\\n` +
      `/start - 开始使用\\n` +
      `/help - 显示此帮助\\n` +
      `/token - 查看您的访问令牌\\n` +
      `/files - 查看最近上传的文件\\n` +
      `/stats - 查看统计信息\\n\\n` +
      `🔗 *文件链接格式*\\n` +
      `\\`/file/{file_id}/original\\` - 原图\\n` +
      `\\`/file/{file_id}/standard\\` - 标准质量\\n` +
      `\\`/file/{file_id}/low\\` - 低质量`;

    await this.service.sendMessage(chatId, helpText);
  }

  private async showUserFiles(chatId: number, user: User): Promise<void> {
    const mediaRepo = new MediaFileRepository(this.env.DB);
    const files = await mediaRepo.findByUserId(user.id, 10, 0);

    if (files.length === 0) {
      await this.service.sendMessage(chatId, '您还没有上传任何文件。');
      return;
    }

    const keyboard = {
      inline_keyboard: files.map((f) => [
        {
          text: `${f.original_filename} (${(f.file_size / 1024).toFixed(1)}KB)`,
          callback_data: `file:${f.file_id}`,
        },
      ]),
    };

    await this.service.sendMessage(
      chatId,
      `您最近上传的 ${files.length} 个文件：`,
      keyboard
    );
  }

  private async showStats(chatId: number, user: User): Promise<void> {
    const mediaRepo = new MediaFileRepository(this.env.DB);
    const files = await mediaRepo.findByUserId(user.id, 1000, 0);

    const totalSize = files.reduce((sum, f) => sum + f.file_size, 0);
    const totalViews = files.reduce((sum, f) => sum + f.view_count, 0);
    const activeFiles = files.filter((f) => f.is_deleted !== 1 && f.is_expired !== 1).length;

    const statsText = `📊 *统计信息*\\n\\n` +
      `文件总数: ${files.length}\\n` +
      `有效文件: ${activeFiles}\\n` +
      `总大小: ${(totalSize / 1024 / 1024).toFixed(2)} MB\\n` +
      `总访问量: ${totalViews}`;

    await this.service.sendMessage(chatId, statsText);
  }

  private async handlePhotoUpload(chatId: number, user: User, message: TelegramMessage): Promise<void> {
    const photos = message.photo || [];
    const largestPhoto = photos[photos.length - 1];
    
    if (!largestPhoto) {
      await this.service.sendMessage(chatId, '无法处理图片。');
      return;
    }

    const telegramFileId = largestPhoto.file_id;
    const fileSize = largestPhoto.file_size || 0;
    const caption = message.caption || 'photo.jpg';

    let telegramMessageId: number | undefined;
    let storedTelegramFileId = telegramFileId;

    if (this.channelId) {
      try {
        const result = await this.service.sendPhoto(
          this.channelId,
          telegramFileId,
          `User: ${user.username} (${user.id})`
        );
        telegramMessageId = result.messageId;
        storedTelegramFileId = result.fileId || telegramFileId;
      } catch (e) {
        console.error('Failed to store photo in channel:', e);
      }
    }

    const fileId = generateFileId();
    const mediaRepo = new MediaFileRepository(this.env.DB);

    const mediaFile = await mediaRepo.create({
      file_id: fileId,
      user_id: user.id,
      original_filename: caption,
      media_type: 'image' as MediaType,
      mime_type: 'image/jpeg',
      file_size: fileSize,
      width: largestPhoto.width,
      height: largestPhoto.height,
      original_path: `telegram:${storedTelegramFileId}`,
      original_size: fileSize,
      telegram_file_id: storedTelegramFileId,
      telegram_message_id: telegramMessageId,
      is_public: 1,
      require_token: 0,
    });

    const baseUrl = this.env.ENVIRONMENT === 'production'
      ? `https://${new URL(this.env.TELEGRAM_WEBHOOK_SECRET || '').host || 'example.com'}`
      : 'http://localhost:8787';

    const fileUrl = `${baseUrl}/file/${fileId}/original`;

    await this.service.sendMessage(
      chatId,
      `✅ 上传成功！\\n\\n` +
        `文件名: \`${caption}\`\\n` +
        `文件ID: \`${fileId}\`\\n\\n` +
        `访问链接:\\n${fileUrl}`
    );
  }

  private async handleDocumentUpload(chatId: number, user: User, message: TelegramMessage): Promise<void> {
    const doc = message.document;
    if (!doc) {
      await this.service.sendMessage(chatId, '无法处理文档。');
      return;
    }

    const telegramFileId = doc.file_id;
    const fileSize = doc.file_size || 0;
    const filename = doc.file_name || 'document';
    const mimeType = doc.mime_type || 'application/octet-stream';

    const isImage = mimeType.startsWith('image/');
    const isVideo = mimeType.startsWith('video/');
    const mediaType: MediaType = isImage ? 'image' : isVideo ? 'video' : 'image';

    let telegramMessageId: number | undefined;
    let storedTelegramFileId = telegramFileId;

    if (this.channelId) {
      try {
        const result = await this.service.sendDocument(
          this.channelId,
          telegramFileId,
          `User: ${user.username} (${user.id}) - ${filename}`
        );
        telegramMessageId = result.messageId;
        storedTelegramFileId = result.fileId || telegramFileId;
      } catch (e) {
        console.error('Failed to store document in channel:', e);
      }
    }

    const fileId = generateFileId();
    const mediaRepo = new MediaFileRepository(this.env.DB);

    const mediaFile = await mediaRepo.create({
      file_id: fileId,
      user_id: user.id,
      original_filename: filename,
      media_type: mediaType,
      mime_type: mimeType,
      file_size: fileSize,
      original_path: `telegram:${storedTelegramFileId}`,
      original_size: fileSize,
      telegram_file_id: storedTelegramFileId,
      telegram_message_id: telegramMessageId,
      is_public: 1,
      require_token: 0,
    });

    const baseUrl = this.env.ENVIRONMENT === 'production'
      ? `https://${new URL(this.env.TELEGRAM_WEBHOOK_SECRET || '').host || 'example.com'}`
      : 'http://localhost:8787';

    const fileUrl = `${baseUrl}/file/${fileId}/original`;

    await this.service.sendMessage(
      chatId,
      `✅ 上传成功！\\n\\n` +
        `文件名: \`${filename}\`\\n` +
        `文件ID: \`${fileId}\`\\n\\n` +
        `访问链接:\\n${fileUrl}`
    );
  }

  private async handleVideoUpload(chatId: number, user: User, message: TelegramMessage): Promise<void> {
    const video = message.video;
    if (!video) {
      await this.service.sendMessage(chatId, '无法处理视频。');
      return;
    }

    const telegramFileId = video.file_id;
    const fileSize = video.file_size || 0;
    const mimeType = video.mime_type || 'video/mp4';

    let telegramMessageId: number | undefined;
    let storedTelegramFileId = telegramFileId;

    if (this.channelId) {
      try {
        const result = await this.service.sendVideo(
          this.channelId,
          telegramFileId,
          `User: ${user.username} (${user.id})`
        );
        telegramMessageId = result.messageId;
        storedTelegramFileId = result.fileId || telegramFileId;
      } catch (e) {
        console.error('Failed to store video in channel:', e);
      }
    }

    const fileId = generateFileId();
    const mediaRepo = new MediaFileRepository(this.env.DB);

    const mediaFile = await mediaRepo.create({
      file_id: fileId,
      user_id: user.id,
      original_filename: `video_${Date.now()}.mp4`,
      media_type: 'video' as MediaType,
      mime_type: mimeType,
      file_size: fileSize,
      width: video.width,
      height: video.height,
      original_path: `telegram:${storedTelegramFileId}`,
      original_size: fileSize,
      telegram_file_id: storedTelegramFileId,
      telegram_message_id: telegramMessageId,
      is_public: 1,
      require_token: 0,
    });

    const baseUrl = this.env.ENVIRONMENT === 'production'
      ? `https://${new URL(this.env.TELEGRAM_WEBHOOK_SECRET || '').host || 'example.com'}`
      : 'http://localhost:8787';

    const fileUrl = `${baseUrl}/file/${fileId}/original`;

    await this.service.sendMessage(
      chatId,
      `✅ 上传成功！\\n\\n` +
        `视频已上传\\n` +
        `文件ID: \`${fileId}\`\\n\\n` +
        `访问链接:\\n${fileUrl}`
    );
  }
}
