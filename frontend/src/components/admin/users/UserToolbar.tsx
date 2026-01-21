/**
 * UserToolbar - Search, filter, batch actions and export
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Search, Download, Ban, UserCheck, Trash2, X, Loader2 } from 'lucide-react';
import type { AdminFlagFilter, UserStatusFilter, AdminUserBatchAction } from '@/types/adminUser';

interface UserToolbarProps {
  search: string;
  onSearchChange: (value: string) => void;
  statusFilter: UserStatusFilter;
  onStatusFilterChange: (value: UserStatusFilter) => void;
  adminFilter: AdminFlagFilter;
  onAdminFilterChange: (value: AdminFlagFilter) => void;
  selectedCount: number;
  onBatchAction: (action: AdminUserBatchAction) => Promise<void>;
  onExport: () => Promise<void>;
  isExporting?: boolean;
  isBatchLoading?: boolean;
}

export function UserToolbar({
  search,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  adminFilter,
  onAdminFilterChange,
  selectedCount,
  onBatchAction,
  onExport,
  isExporting = false,
  isBatchLoading = false,
}: UserToolbarProps) {
  const { t } = useTranslation('common');
  const [confirmAction, setConfirmAction] = useState<AdminUserBatchAction | null>(null);

  const handleBatchConfirm = async () => {
    if (confirmAction) {
      await onBatchAction(confirmAction);
      setConfirmAction(null);
    }
  };

  const getActionLabel = (action: AdminUserBatchAction) => {
    switch (action) {
      case 'ban':
        return t('admin.users.action.ban', 'Ban');
      case 'unban':
        return t('admin.users.action.unban', 'Unban');
      case 'delete':
        return t('admin.users.action.delete', 'Delete');
    }
  };

  return (
    <>
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        {/* Search and Filters */}
        <div className="flex flex-1 flex-col gap-2 sm:flex-row sm:items-center">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder={t('admin.users.search_placeholder', 'Search by nickname or email...')}
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-9"
            />
            {search && (
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-1 top-1/2 -translate-y-1/2 h-6 w-6"
                onClick={() => onSearchChange('')}
              >
                <X className="h-3 w-3" />
              </Button>
            )}
          </div>

          <Select value={statusFilter} onValueChange={(v) => onStatusFilterChange(v as UserStatusFilter)}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder={t('admin.users.filter.status', 'Status')} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t('admin.users.filter.all', 'All')}</SelectItem>
              <SelectItem value="active">{t('admin.users.filter.active', 'Active')}</SelectItem>
              <SelectItem value="banned">{t('admin.users.filter.banned', 'Banned')}</SelectItem>
            </SelectContent>
          </Select>

          <Select value={adminFilter} onValueChange={(v) => onAdminFilterChange(v as AdminFlagFilter)}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder={t('admin.users.filter.role', 'Role')} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t('admin.users.filter.all', 'All')}</SelectItem>
              <SelectItem value="yes">{t('admin.users.filter.admin', 'Admin')}</SelectItem>
              <SelectItem value="no">{t('admin.users.filter.user', 'User')}</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {selectedCount > 0 && (
            <>
              <span className="text-sm text-muted-foreground mr-2">
                {t('admin.users.selected', '{{count}} selected', { count: selectedCount })}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setConfirmAction('ban')}
                disabled={isBatchLoading}
              >
                <Ban className="h-4 w-4 mr-1" />
                {t('admin.users.action.ban', 'Ban')}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setConfirmAction('unban')}
                disabled={isBatchLoading}
              >
                <UserCheck className="h-4 w-4 mr-1" />
                {t('admin.users.action.unban', 'Unban')}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setConfirmAction('delete')}
                disabled={isBatchLoading}
                className="text-destructive hover:text-destructive"
              >
                <Trash2 className="h-4 w-4 mr-1" />
                {t('admin.users.action.delete', 'Delete')}
              </Button>
            </>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={onExport}
            disabled={isExporting}
          >
            {isExporting ? (
              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <Download className="h-4 w-4 mr-1" />
            )}
            {t('admin.users.export', 'Export')}
          </Button>
        </div>
      </div>

      {/* Confirm Dialog */}
      <AlertDialog open={confirmAction !== null} onOpenChange={() => setConfirmAction(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {t('admin.users.confirm_title', 'Confirm Action')}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {t('admin.users.confirm_description', 'Are you sure you want to {{action}} {{count}} user(s)? This action cannot be undone.', {
                action: confirmAction ? getActionLabel(confirmAction).toLowerCase() : '',
                count: selectedCount,
              })}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isBatchLoading}>
              {t('common.cancel', 'Cancel')}
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleBatchConfirm}
              disabled={isBatchLoading}
              className={confirmAction === 'delete' ? 'bg-destructive hover:bg-destructive/90' : ''}
            >
              {isBatchLoading && <Loader2 className="h-4 w-4 mr-1 animate-spin" />}
              {confirmAction ? getActionLabel(confirmAction) : ''}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

export default UserToolbar;
