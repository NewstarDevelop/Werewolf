/**
 * Admin user management type definitions
 */

export interface AdminUser {
  id: string;
  nickname: string;
  email: string | null;
  avatar_url: string | null;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface AdminUserDetail extends AdminUser {
  bio: string | null;
  is_email_verified: boolean;
  updated_at: string;
  preferences: Record<string, unknown>;
}

export type UserStatusFilter = 'active' | 'banned' | 'all';
export type AdminFlagFilter = 'yes' | 'no' | 'all';
export type UserSort = 'created_at_desc' | 'last_login_at_desc' | 'id_asc';
export type AdminUserBatchAction = 'ban' | 'unban' | 'delete';

export interface AdminUserListParams {
  q?: string;
  status?: UserStatusFilter;
  admin?: AdminFlagFilter;
  sort?: UserSort;
  page?: number;
  page_size?: number;
}

export interface AdminUserListResponse {
  items: AdminUser[];
  total: number;
  page: number;
  page_size: number;
}

export interface AdminUpdateUserProfileRequest {
  nickname?: string;
  bio?: string;
  avatar_url?: string;
}

export interface AdminSetUserActiveRequest {
  is_active: boolean;
}

export interface AdminSetUserAdminRequest {
  is_admin: boolean;
}

export interface AdminUserBatchRequest {
  action: AdminUserBatchAction;
  ids: string[];
}

export interface AdminUserBatchResponse {
  accepted: number;
  updated: number;
  failed: string[];
}
