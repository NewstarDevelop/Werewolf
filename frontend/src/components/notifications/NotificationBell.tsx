/**
 * NotificationBell - Bell icon with unread count badge
 */
import { Bell } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface NotificationBellProps {
  count: number;
  onClick?: () => void;
  className?: string;
}

export function NotificationBell({
  count,
  onClick,
  className,
}: NotificationBellProps) {
  const hasUnread = count > 0;

  return (
    <Button
      variant="ghost"
      size="icon"
      className={cn('relative', className)}
      onClick={onClick}
      aria-label={`Notifications${hasUnread ? ` (${count} unread)` : ''}`}
    >
      <Bell className="h-5 w-5" />
      {hasUnread && (
        <span
          className={cn(
            'absolute -top-0.5 -right-0.5 flex items-center justify-center',
            'min-w-[18px] h-[18px] px-1 text-[10px] font-bold',
            'bg-destructive text-destructive-foreground rounded-full',
            'animate-in zoom-in-50 duration-200'
          )}
        >
          {count > 99 ? '99+' : count}
        </span>
      )}
    </Button>
  );
}

export default NotificationBell;
