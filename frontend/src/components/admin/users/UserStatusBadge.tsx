/**
 * UserStatusBadge - Display user status and admin badge
 */

import { Badge } from '@/components/ui/badge';
import { Shield, ShieldOff, UserCheck, UserX } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface UserStatusBadgeProps {
  isActive: boolean;
  isAdmin?: boolean;
  showAdmin?: boolean;
}

export function UserStatusBadge({ isActive, isAdmin, showAdmin = true }: UserStatusBadgeProps) {
  const { t } = useTranslation('common');

  return (
    <div className="flex items-center gap-1.5">
      {isActive ? (
        <Badge variant="outline" className="text-green-600 border-green-300 bg-green-50 dark:bg-green-950/30">
          <UserCheck className="h-3 w-3 mr-1" />
          {t('admin.users.status.active', 'Active')}
        </Badge>
      ) : (
        <Badge variant="outline" className="text-red-600 border-red-300 bg-red-50 dark:bg-red-950/30">
          <UserX className="h-3 w-3 mr-1" />
          {t('admin.users.status.banned', 'Banned')}
        </Badge>
      )}
      {showAdmin && isAdmin && (
        <Badge variant="secondary" className="text-amber-600 border-amber-300 bg-amber-50 dark:bg-amber-950/30">
          <Shield className="h-3 w-3 mr-1" />
          {t('admin.users.role.admin', 'Admin')}
        </Badge>
      )}
    </div>
  );
}

export function AdminBadge({ isAdmin }: { isAdmin: boolean }) {
  const { t } = useTranslation('common');

  if (isAdmin) {
    return (
      <Badge variant="secondary" className="text-amber-600 border-amber-300 bg-amber-50 dark:bg-amber-950/30">
        <Shield className="h-3 w-3 mr-1" />
        {t('admin.users.role.admin', 'Admin')}
      </Badge>
    );
  }

  return (
    <Badge variant="outline" className="text-muted-foreground">
      <ShieldOff className="h-3 w-3 mr-1" />
      {t('admin.users.role.user', 'User')}
    </Badge>
  );
}

export default UserStatusBadge;
