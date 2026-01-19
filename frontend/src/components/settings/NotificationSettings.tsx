/**
 * NotificationSettings Component
 * Settings panel for notification preferences by category
 */
import { useEffect, useState } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Bell, Gamepad2, Users, Info, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getUserPreferences,
  updateUserPreferences,
  type UserPreferences,
} from '@/services/preferencesApi';
import { toast } from 'sonner';
import type { NotificationPreferences } from '@/types/notification';

// Default notification preferences
const DEFAULT_NOTIFICATION_PREFS: NotificationPreferences = {
  GAME: true,
  ROOM: true,
  SOCIAL: true,
  SYSTEM: true,
};

// Category configuration
const CATEGORIES: {
  key: keyof NotificationPreferences;
  icon: React.ComponentType<{ className?: string }>;
  labelKey: string;
  descKey: string;
  defaultLabel: string;
  defaultDesc: string;
}[] = [
  {
    key: 'GAME',
    icon: Gamepad2,
    labelKey: 'settings.notifications_game',
    descKey: 'settings.notifications_game_desc',
    defaultLabel: '游戏通知',
    defaultDesc: '游戏开始、结束等事件提醒',
  },
  {
    key: 'ROOM',
    icon: Users,
    labelKey: 'settings.notifications_room',
    descKey: 'settings.notifications_room_desc',
    defaultLabel: '房间通知',
    defaultDesc: '玩家加入、房间创建等事件提醒',
  },
  {
    key: 'SOCIAL',
    icon: Users,
    labelKey: 'settings.notifications_social',
    descKey: 'settings.notifications_social_desc',
    defaultLabel: '社交通知',
    defaultDesc: '好友请求等社交事件提醒',
  },
  {
    key: 'SYSTEM',
    icon: Info,
    labelKey: 'settings.notifications_system',
    descKey: 'settings.notifications_system_desc',
    defaultLabel: '系统通知',
    defaultDesc: '系统公告、维护提醒等',
  },
];

export function NotificationSettings() {
  const { t } = useTranslation('common');
  const queryClient = useQueryClient();

  // Local state for optimistic updates
  const [localPrefs, setLocalPrefs] = useState<NotificationPreferences>(
    DEFAULT_NOTIFICATION_PREFS
  );

  // Fetch user preferences
  const { data: preferences, isLoading } = useQuery({
    queryKey: ['userPreferences'],
    queryFn: getUserPreferences,
  });

  // Sync local state when preferences load
  useEffect(() => {
    if (preferences?.notifications) {
      setLocalPrefs({
        ...DEFAULT_NOTIFICATION_PREFS,
        ...preferences.notifications,
      });
    }
  }, [preferences]);

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: updateUserPreferences,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['userPreferences'] });
    },
    onError: () => {
      toast.error(t('settings.save_error', '保存失败，请重试'));
      // Rollback to server state
      if (preferences?.notifications) {
        setLocalPrefs({
          ...DEFAULT_NOTIFICATION_PREFS,
          ...preferences.notifications,
        });
      }
    },
  });

  // Handle toggle change
  const handleToggle = (category: keyof NotificationPreferences) => {
    const newValue = !localPrefs[category];
    const newPrefs = { ...localPrefs, [category]: newValue };

    // Optimistic update
    setLocalPrefs(newPrefs);

    // Save to server
    const fullPrefs: UserPreferences = {
      sound_effects: preferences?.sound_effects ?? {
        enabled: true,
        volume: 1.0,
        muted: false,
      },
      notifications: newPrefs,
    };

    updateMutation.mutate(fullPrefs);
  };

  if (isLoading) {
    return (
      <Card className="glass-panel">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-accent-foreground">
            <Bell className="h-5 w-5" aria-hidden="true" />
            {t('settings.notifications', '通知')}
          </CardTitle>
          <CardDescription>
            {t('settings.notifications_desc', '管理通知偏好设置')}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass-panel">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-accent-foreground">
          <Bell className="h-5 w-5" aria-hidden="true" />
          {t('settings.notifications', '通知')}
        </CardTitle>
        <CardDescription>
          {t('settings.notifications_desc', '管理通知偏好设置')}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {CATEGORIES.map((category) => {
          const Icon = category.icon;
          const isEnabled = localPrefs[category.key];

          return (
            <div
              key={category.key}
              className="flex items-center justify-between rounded-lg border border-border p-4"
            >
              <div className="flex items-center gap-3">
                <Icon
                  className="h-5 w-5 text-muted-foreground"
                  aria-hidden="true"
                />
                <div className="space-y-1">
                  <p className="text-sm font-medium">
                    {t(category.labelKey, category.defaultLabel)}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {t(category.descKey, category.defaultDesc)}
                  </p>
                </div>
              </div>
              <Switch
                checked={isEnabled}
                onCheckedChange={() => handleToggle(category.key)}
                disabled={updateMutation.isPending}
                aria-label={t(category.labelKey, category.defaultLabel)}
              />
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

export default NotificationSettings;
