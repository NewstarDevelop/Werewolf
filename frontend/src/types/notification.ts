/**
 * Notification type definitions
 * Matches backend app/schemas/notification.py
 */

export enum NotificationCategory {
  GAME = 'GAME',
  ROOM = 'ROOM',
  SOCIAL = 'SOCIAL',
  SYSTEM = 'SYSTEM',
}

export interface Notification {
  id: string;
  user_id: string;
  category: NotificationCategory;
  title: string;
  body: string;
  data: Record<string, unknown>;
  created_at: string;
  read_at: string | null;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  page: number;
  page_size: number;
}

export interface UnreadCountResponse {
  unread_count: number;
}

export interface MarkReadResponse {
  notification_id: string;
  read_at: string;
}

export interface ReadAllResponse {
  updated: number;
  read_at: string;
}

export interface ReadBatchRequest {
  notification_ids: string[];
}

export interface ReadBatchResponse {
  updated: number;
  read_at: string;
}

/**
 * WebSocket message types
 */
export interface NotificationWSMessage {
  type: 'connected' | 'notification' | 'pong' | 'error';
  data: NotificationWSData;
}

export interface NotificationWSData {
  user_id?: string;
  unread_count?: number;
  persisted?: boolean;
  notification?: Notification;
  event_id?: string;
}

/**
 * Notification preferences (per-category toggles)
 */
export interface NotificationPreferences {
  GAME: boolean;
  ROOM: boolean;
  SOCIAL: boolean;
  SYSTEM: boolean;
}
