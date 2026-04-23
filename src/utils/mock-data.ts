import type { MockUser, MockMediaFile, MediaType } from '../types';
import { generateUUID, generateSecretToken, generateFileId, hashPassword } from './security';

export const MOCK_USERS: MockUser[] = [
  {
    username: 'admin',
    email: 'admin@imgbed.local',
    password: 'admin123',
    is_admin: true,
  },
  {
    username: 'demo_user',
    email: 'demo@imgbed.local',
    password: 'demo123',
  },
  {
    username: 'test_user_01',
    email: 'test01@imgbed.local',
    password: 'test123',
  },
  {
    username: 'john_doe',
    email: 'john@example.com',
    password: 'password123',
  },
  {
    username: 'jane_smith',
    email: 'jane@example.com',
    password: 'password456',
  },
];

const imageMimeTypes = [
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
];

const videoMimeTypes = [
  'video/mp4',
  'video/webm',
];

const imageFilenames = [
  'sunset_landscape.jpg',
  'mountain_view.png',
  'city_skyline.webp',
  'beach_sunrise.jpg',
  'forest_trail.png',
  'ocean_waves.webp',
  'snowy_mountain.jpg',
  'spring_flowers.png',
  'autumn_forest.jpg',
  'summer_beach.webp',
  'night_city.jpg',
  'desert_sunset.png',
  'waterfall_canyon.jpg',
  'garden_spring.webp',
  'lake_mountain.jpg',
];

const videoFilenames = [
  'nature_documentary.mp4',
  'travel_vlog.webm',
  'city_timelapse.mp4',
  'ocean_waves.mp4',
  'mountain_hike.webm',
];

function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randomChoice<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randomDate(daysAgo: number): string {
  const date = new Date();
  date.setDate(date.getDate() - randomInt(0, daysAgo));
  return date.toISOString();
}

export function generateMockMediaFiles(count: number, userId: number, userUuid: string): MockMediaFile[] {
  const files: MockMediaFile[] = [];
  const isImage = Math.random() > 0.2;
  
  for (let i = 0; i < count; i++) {
    const mediaType: MediaType = isImage && Math.random() > 0.15 ? 'image' : 'video';
    const mimeTypes = mediaType === 'image' ? imageMimeTypes : videoMimeTypes;
    const filenames = mediaType === 'image' ? imageFilenames : videoFilenames;
    
    files.push({
      filename: randomChoice(filenames),
      media_type: mediaType,
      mime_type: randomChoice(mimeTypes),
      width: mediaType === 'image' ? randomInt(800, 3840) : undefined,
      height: mediaType === 'image' ? randomInt(600, 2160) : undefined,
      view_count: randomInt(0, 1000),
    });
  }
  
  return files;
}

export async function generateMockData(): Promise<{
  users: Array<{
    uuid: string;
    username: string;
    email: string;
    password_hash: string;
    secret_token: string;
    is_active: number;
    is_admin: number;
    files: Array<{
      file_id: string;
      original_filename: string;
      media_type: MediaType;
      mime_type: string;
      file_size: number;
      width: number | undefined;
      height: number | undefined;
      original_path: string;
      original_size: number;
      view_count: number;
      created_at: string;
      expires_at: string | null;
      is_expired: number;
      is_deleted: number;
      require_token: number;
    }>;
  }>;
}> {
  const users = [];
  
  for (const mockUser of MOCK_USERS) {
    const passwordHash = await hashPassword(mockUser.password);
    const uuid = generateUUID();
    const fileCount = mockUser.is_admin ? 15 : randomInt(5, 20);
    const mockFiles = generateMockMediaFiles(fileCount, 0, uuid);
    
    const files = mockFiles.map((f, index) => {
      const fileId = generateFileId();
      const baseFilename = fileId;
      const ext = f.filename.split('.').pop() || '.jpg';
      const uuidParts = uuid.split('-').slice(0, 2).join('/');
      
      const isExpired = !mockUser.is_admin && Math.random() > 0.7;
      const isDeleted = !mockUser.is_admin && Math.random() > 0.9;
      const requiresToken = Math.random() > 0.8;
      
      const createdDate = randomDate(90);
      let expiresAt: string | null = null;
      
      if (isExpired) {
        const expireDate = new Date(createdDate);
        expireDate.setDate(expireDate.getDate() + randomInt(1, 30));
        expiresAt = expireDate.toISOString();
      }
      
      return {
        file_id: fileId,
        original_filename: f.filename,
        media_type: f.media_type,
        mime_type: f.mime_type,
        file_size: f.media_type === 'image' 
          ? randomInt(100 * 1024, 10 * 1024 * 1024)
          : randomInt(1 * 1024 * 1024, 50 * 1024 * 1024),
        width: f.width,
        height: f.height,
        original_path: `${uuidParts}/${baseFilename}_original.${ext}`,
        original_size: f.media_type === 'image' 
          ? randomInt(100 * 1024, 10 * 1024 * 1024)
          : randomInt(1 * 1024 * 1024, 50 * 1024 * 1024),
        view_count: f.view_count || 0,
        created_at: createdDate,
        expires_at: expiresAt,
        is_expired: isExpired ? 1 : 0,
        is_deleted: isDeleted ? 1 : 0,
        require_token: requiresToken ? 1 : 0,
      };
    });
    
    users.push({
      uuid,
      username: mockUser.username,
      email: mockUser.email,
      password_hash: passwordHash,
      secret_token: generateSecretToken(),
      is_active: 1,
      is_admin: mockUser.is_admin ? 1 : 0,
      files,
    });
  }
  
  return { users };
}

export const MOCK_DATA_SQL = `
-- Mock Users
INSERT INTO users (uuid, username, email, password_hash, secret_token, is_active, is_admin, created_at, updated_at)
VALUES 
  ('550e8400-e29b-41d4-a716-446655440000', 'admin', 'admin@imgbed.local', '$2a$10$placeholder_hash_admin', 'admin_secret_token_12345678901234567890', 1, 1, datetime('now'), datetime('now')),
  ('660e8400-e29b-41d4-a716-446655440000', 'demo_user', 'demo@imgbed.local', '$2a$10$placeholder_hash_demo', 'demo_secret_token_123456789012345678901', 1, 0, datetime('now', '-7 days'), datetime('now', '-7 days')),
  ('770e8400-e29b-41d4-a716-446655440000', 'test_user_01', 'test01@imgbed.local', '$2a$10$placeholder_hash_test', 'test_secret_token_1234567890123456789012', 1, 0, datetime('now', '-14 days'), datetime('now', '-14 days'));

-- Demo mock media files
INSERT INTO media_files (file_id, user_id, original_filename, media_type, mime_type, file_size, width, height, original_path, original_size, view_count, created_at, is_public, require_token, is_expired, is_deleted)
VALUES
  ('demo_file_001', 2, 'sunset_landscape.jpg', 'image', 'image/jpeg', 2456789, 1920, 1080, '660e/8400/demo_original.jpg', 2456789, 156, datetime('now', '-3 days'), 1, 0, 0, 0),
  ('demo_file_002', 2, 'mountain_view.png', 'image', 'image/png', 5678901, 2560, 1440, '660e/8400/demo2_original.png', 5678901, 89, datetime('now', '-5 days'), 1, 0, 0, 0),
  ('demo_file_003', 2, 'nature_video.mp4', 'video', 'video/mp4', 15678901, NULL, NULL, '660e/8400/video_original.mp4', 15678901, 234, datetime('now', '-10 days'), 1, 1, 0, 0),
  ('demo_file_004', 3, 'city_skyline.webp', 'image', 'image/webp', 1234567, 3840, 2160, '770e/8400/city_original.webp', 1234567, 45, datetime('now', '-7 days'), 1, 0, 1, 0),
  ('demo_file_005', 3, 'forest_trail.png', 'image', 'image/png', 3456789, 1920, 1080, '770e/8400/forest_original.png', 3456789, 12, datetime('now', '-20 days'), 0, 0, 0, 1);
`;
