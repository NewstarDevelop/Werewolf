/**
 * NotificationList - Notification list with tabs and scroll area
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { CheckCheck, Loader2 } from 'lucide-react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { NotificationItem } from './NotificationItem';
import { useNotifications } from '@/hooks/useNotifications';
import { NotificationCategory, type Notification } from '@/types/notification';

interface NotificationListProps {
  onNotificationClick?: (notification: Notification) => void;
  onClose?: () => void;
}

type TabValue = 'all' | NotificationCategory;

export function NotificationList({
  onNotificationClick,
  onClose,
}: NotificationListProps) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<TabValue>('all');

  // Get category filter based on active tab
  const categoryFilter =
    activeTab === 'all' ? undefined : (activeTab as NotificationCategory);

  const {
    notifications,
    unreadCount,
    isLoading,
    markAsRead,
    markAllAsRead,
  } = useNotifications({
    category: categoryFilter,
    pageSize: 50,
  });

  const handleNotificationClick = async (notification: Notification) => {
    // Mark as read if unread
    if (!notification.read_at) {
      await markAsRead(notification.id);
    }

    // Call external handler
    if (onNotificationClick) {
      onNotificationClick(notification);
    }

    // Close panel
    if (onClose) {
      onClose();
    }
  };

  const handleMarkAllAsRead = async () => {
    await markAllAsRead();
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <h3 className="font-semibold text-foreground">
          {t('notifications.title', '通知')}
          {unreadCount > 0 && (
            <span className="ml-2 text-sm text-muted-foreground">
              ({unreadCount} {t('notifications.unread', '未读')})
            </span>
          )}
        </h3>
        {unreadCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleMarkAllAsRead}
            className="text-xs"
          >
            <CheckCheck className="h-4 w-4 mr-1" />
            {t('notifications.markAllRead', '全部已读')}
          </Button>
        )}
      </div>

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={(v) => setActiveTab(v as TabValue)}
        className="flex-1 flex flex-col"
      >
        <TabsList className="grid w-full grid-cols-5 h-9 px-2">
          <TabsTrigger value="all" className="text-xs">
            {t('notifications.all', '全部')}
          </TabsTrigger>
          <TabsTrigger value="GAME" className="text-xs">
            {t('notifications.game', '游戏')}
          </TabsTrigger>
          <TabsTrigger value="ROOM" className="text-xs">
            {t('notifications.room', '房间')}
          </TabsTrigger>
          <TabsTrigger value="SOCIAL" className="text-xs">
            {t('notifications.social', '社交')}
          </TabsTrigger>
          <TabsTrigger value="SYSTEM" className="text-xs">
            {t('notifications.system', '系统')}
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="flex-1 mt-0">
          <ScrollArea className="h-[350px]">
            {isLoading ? (
              <div className="flex items-center justify-center h-32">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : notifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
                <p className="text-sm">
                  {t('notifications.empty', '暂无通知')}
                </p>
              </div>
            ) : (
              <div className="divide-y">
                {notifications.map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onClick={handleNotificationClick}
                  />
                ))}
              </div>
            )}
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default NotificationList;
