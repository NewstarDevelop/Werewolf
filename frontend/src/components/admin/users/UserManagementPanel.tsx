/**
 * UserManagementPanel - Main container for user management
 */

import { useState, useCallback, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Users, ChevronLeft, ChevronRight } from 'lucide-react';
import { UserToolbar } from './UserToolbar';
import { UserTable } from './UserTable';
import { UserDetailSheet } from './UserDetailSheet';
import { adminService } from '@/services/adminService';
import { toast } from 'sonner';
import type {
  AdminUser,
  AdminUserListParams,
  UserStatusFilter,
  AdminFlagFilter,
  AdminUserBatchAction,
} from '@/types/adminUser';

interface UserManagementPanelProps {
  token?: string;
}

export function UserManagementPanel({ token }: UserManagementPanelProps) {
  const { t } = useTranslation('common');

  // List state
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [isLoading, setIsLoading] = useState(false);

  // Filter state
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<UserStatusFilter>('all');
  const [adminFilter, setAdminFilter] = useState<AdminFlagFilter>('all');

  // Selection state
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Sheet state
  const [sheetUserId, setSheetUserId] = useState<string | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [sheetTab, setSheetTab] = useState<'overview' | 'edit' | 'danger'>('overview');

  // Loading states
  const [isExporting, setIsExporting] = useState(false);
  const [isBatchLoading, setIsBatchLoading] = useState(false);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  // Fetch users
  const fetchUsers = useCallback(async () => {
    setIsLoading(true);
    try {
      const params: AdminUserListParams = {
        page,
        page_size: pageSize,
        status: statusFilter,
        admin: adminFilter,
      };
      if (debouncedSearch) {
        params.q = debouncedSearch;
      }

      const response = await adminService.getUsers(params, token);
      setUsers(response.items);
      setTotal(response.total);
    } catch (err) {
      toast.error((err as Error).message || 'Failed to fetch users');
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, debouncedSearch, statusFilter, adminFilter, token]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  // Reset selection when filters change
  useEffect(() => {
    setSelectedIds(new Set());
  }, [debouncedSearch, statusFilter, adminFilter, page]);

  // Handlers
  const handleViewDetail = (user: AdminUser) => {
    setSheetUserId(user.id);
    setSheetTab('overview');
    setSheetOpen(true);
  };

  const handleEdit = (user: AdminUser) => {
    setSheetUserId(user.id);
    setSheetTab('edit');
    setSheetOpen(true);
  };

  const handleToggleStatus = async (user: AdminUser) => {
    try {
      await adminService.setUserStatus(user.id, { is_active: !user.is_active }, token);
      toast.success(
        user.is_active
          ? t('admin.users.banned', 'User has been banned')
          : t('admin.users.unbanned', 'User has been unbanned')
      );
      fetchUsers();
    } catch (err) {
      toast.error((err as Error).message || 'Failed to update status');
    }
  };

  const handleToggleAdmin = async (user: AdminUser) => {
    try {
      await adminService.setUserAdmin(user.id, { is_admin: !user.is_admin }, token);
      toast.success(
        user.is_admin
          ? t('admin.users.admin_revoked', 'Admin privileges revoked')
          : t('admin.users.admin_granted', 'Admin privileges granted')
      );
      fetchUsers();
    } catch (err) {
      toast.error((err as Error).message || 'Failed to update admin status');
    }
  };

  const handleBatchAction = async (action: AdminUserBatchAction) => {
    if (selectedIds.size === 0) return;

    setIsBatchLoading(true);
    try {
      const response = await adminService.batchUsers(
        { action, ids: Array.from(selectedIds) },
        token
      );
      toast.success(
        t('admin.users.batch_success', '{{updated}} of {{accepted}} users updated', {
          updated: response.updated,
          accepted: response.accepted,
        })
      );
      if (response.failed.length > 0) {
        toast.warning(
          t('admin.users.batch_partial', '{{count}} users could not be updated', {
            count: response.failed.length,
          })
        );
      }
      setSelectedIds(new Set());
      fetchUsers();
    } catch (err) {
      toast.error((err as Error).message || 'Batch operation failed');
    } finally {
      setIsBatchLoading(false);
    }
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const params: AdminUserListParams = {
        status: statusFilter,
        admin: adminFilter,
      };
      if (debouncedSearch) {
        params.q = debouncedSearch;
      }

      const blob = await adminService.exportUsers(params, token);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `users_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast.success(t('admin.users.export_success', 'Users exported successfully'));
    } catch (err) {
      toast.error((err as Error).message || 'Failed to export users');
    } finally {
      setIsExporting(false);
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <>
      <Card className="glass-panel">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            {t('admin.users.title', 'User Management')}
          </CardTitle>
          <CardDescription>
            {t('admin.users.description', 'View and manage registered users')}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <UserToolbar
            search={search}
            onSearchChange={setSearch}
            statusFilter={statusFilter}
            onStatusFilterChange={(v) => {
              setStatusFilter(v);
              setPage(1);
            }}
            adminFilter={adminFilter}
            onAdminFilterChange={(v) => {
              setAdminFilter(v);
              setPage(1);
            }}
            selectedCount={selectedIds.size}
            onBatchAction={handleBatchAction}
            onExport={handleExport}
            isExporting={isExporting}
            isBatchLoading={isBatchLoading}
          />

          <UserTable
            users={users}
            isLoading={isLoading}
            selectedIds={selectedIds}
            onSelectionChange={setSelectedIds}
            onViewDetail={handleViewDetail}
            onEdit={handleEdit}
            onToggleStatus={handleToggleStatus}
            onToggleAdmin={handleToggleAdmin}
          />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {t('admin.users.pagination', 'Showing {{from}}-{{to}} of {{total}}', {
                  from: (page - 1) * pageSize + 1,
                  to: Math.min(page * pageSize, total),
                  total,
                })}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1 || isLoading}
                >
                  <ChevronLeft className="h-4 w-4" />
                  {t('common.previous', 'Previous')}
                </Button>
                <span className="text-sm text-muted-foreground">
                  {page} / {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages || isLoading}
                >
                  {t('common.next', 'Next')}
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <UserDetailSheet
        userId={sheetUserId}
        isOpen={sheetOpen}
        onClose={() => {
          setSheetOpen(false);
          setSheetUserId(null);
        }}
        token={token}
        initialTab={sheetTab}
        onUserUpdated={fetchUsers}
      />
    </>
  );
}

export default UserManagementPanel;
