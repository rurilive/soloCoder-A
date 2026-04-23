export interface Env {
  DB: D1Database;
  MEDIA_BUCKET: R2Bucket;
  
  SECRET_KEY: string;
  JWT_ALGORITHM: string;
  ACCESS_TOKEN_EXPIRE_MINUTES: number;
  
  TELEGRAM_BOT_TOKEN: string;
  TELEGRAM_CHANNEL_ID: string;
  TELEGRAM_WEBHOOK_SECRET: string;
  
  MAX_FILE_SIZE: number;
  ALLOWED_IMAGE_TYPES: string;
  ALLOWED_VIDEO_TYPES: string;
  
  ENVIRONMENT: string;
}

export interface User {
  id: number;
  uuid: string;
  username: string;
  email: string;
  password_hash: string;
  secret_token: string;
  is_active: number;
  is_admin: number;
  created_at: string;
  updated_at: string;
  telegram_user_id?: number;
}

export interface Session {
  id: number;
  session_id: string;
  user_id: number;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
  expires_at: string;
  last_activity: string;
}

export type MediaType = 'image' | 'video';
export type QualityLevel = 'original' | 'standard' | 'low' | 'icon';

export interface MediaFile {
  id: number;
  file_id: string;
  user_id: number;
  original_filename: string;
  media_type: MediaType;
  mime_type: string;
  file_size: number;
  width?: number;
  height?: number;
  
  original_path: string;
  standard_path?: string;
  low_path?: string;
  icon_path?: string;
  
  original_size: number;
  standard_size?: number;
  low_size?: number;
  icon_size?: number;
  
  telegram_file_id?: string;
  telegram_message_id?: number;
  
  is_public: number;
  view_count: number;
  created_at: string;
  updated_at?: string;
  
  expires_at?: string;
  is_expired: number;
  
  is_deleted: number;
  deleted_at?: string;
  deleted_reason?: string;
  
  require_token: number;
  allowed_referers?: string;
}

export interface JwtPayload {
  sub: string;
  exp: number;
  iat?: number;
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
  data?: T;
  error?: string;
}

export interface UploadResponse {
  success: boolean;
  message: string;
  file?: MediaFileResponse;
}

export interface MediaFileResponse {
  id: number;
  file_id: string;
  original_filename: string;
  media_type: string;
  mime_type: string;
  file_size: number;
  width?: number;
  height?: number;
  view_count: number;
  created_at: string;
  updated_at?: string;
  expires_at?: string;
  is_expired: boolean;
  is_deleted: boolean;
  deleted_at?: string;
  original_url: string;
  standard_url?: string;
  low_url?: string;
  icon_url?: string;
}

export interface TelegramUpdate {
  update_id: number;
  message?: TelegramMessage;
  callback_query?: TelegramCallbackQuery;
}

export interface TelegramMessage {
  message_id: number;
  from: TelegramUser;
  chat: TelegramChat;
  date: number;
  text?: string;
  photo?: TelegramPhotoSize[];
  document?: TelegramDocument;
  video?: TelegramVideo;
  caption?: string;
}

export interface TelegramUser {
  id: number;
  is_bot: boolean;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
}

export interface TelegramChat {
  id: number;
  type: 'private' | 'group' | 'supergroup' | 'channel';
  title?: string;
  username?: string;
}

export interface TelegramPhotoSize {
  file_id: string;
  file_unique_id: string;
  width: number;
  height: number;
  file_size?: number;
}

export interface TelegramDocument {
  file_id: string;
  file_unique_id: string;
  file_name?: string;
  mime_type?: string;
  file_size?: number;
}

export interface TelegramVideo {
  file_id: string;
  file_unique_id: string;
  width: number;
  height: number;
  duration: number;
  mime_type?: string;
  file_size?: number;
}

export interface TelegramCallbackQuery {
  id: string;
  from: TelegramUser;
  message?: TelegramMessage;
  data?: string;
}

export interface MockUser {
  username: string;
  email: string;
  password: string;
  is_admin?: boolean;
}

export interface MockMediaFile {
  filename: string;
  media_type: MediaType;
  mime_type: string;
  width?: number;
  height?: number;
  view_count?: number;
}
