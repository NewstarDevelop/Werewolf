/**
 * useNotifications Hook - Notification list management with TanStack Query
 *
 * Features:
 * - Fetch notification list with pagination and filtering
 * - Mark notifications as read (single, batch, all)
 * - Optimistic updates for better UX
 * - Integration with WebSocket for real-time updates
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';
import {
  listNotifications,
  getUnreadCount,
  markNotificationRead,
  markAllNotificationsRead,
  markNotificationsBatchRead,
  type ListNotificationsParams,
} from '@/services/notificationApi';
import type { Notification, NotificationCategory } from '@/types/notification';

interface UseNotificationsOptions {
  category?: NotificationCategory;
  unreadOnly?: boolean;
  page?: number;
  pageSize?: number;
  enabled?: boolean;
}

interface UseNotificationsReturn {
  // Data
  notifications: Notification[];
  total: number;
  unreadCount: number;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;

  // Actions
  markAsRead: (notificationId: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  markBatchAsRead: (notificationIds: string[]) => Promise<void>;
  refetch: () => Promise<void>;

  // Pagination
  page: number;
  pageSize: number;
  hasMore: boolean;
}

export function useNotifications(
  options: UseNotificationsOptions = {}
): UseNotificationsReturn {
  const {
    category,
    unreadOnly = false,
    page = 1,
    pageSize = 20,
    enabled = true,
  } = options;

  const queryClient = useQueryClient();

  // Build query params
  const queryParams: ListNotificationsParams = useMemo(
    () => ({
      category,
      unread_only: unreadOnly,
      page,
      page_size: pageSize,
    }),
    [category, unreadOnly, page, pageSize]
  );

  // Fetch notifications list
  const {
    data,
    isLoading,
    isError,
    error,
    refetch: refetchList,
  } = useQuery({
    queryKey: ['notifications', queryParams],
    queryFn: () => listNotifications(queryParams),
    enabled,
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: true,
  });

  // Fetch unread count separately for badge display
  const { data: unreadCountData } = useQuery({
    queryKey: ['notifications', 'unreadCount'],
    queryFn: getUnreadCount,
    enabled,
    staleTime: 30000,
    refetchOnWindowFocus: true,
  });

  // Mark single notification as read
  const markAsReadMutation = useMutation({
    mutationFn: markNotificationRead,
    onMutate: async (notificationId) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['notifications'] });

      // Snapshot previous value
      const previousData = queryClient.getQueryData(['notifications', queryParams]);

      // Optimistically update
      queryClient.setQueryData(
        ['notifications', queryParams],
        (old: typeof data) => {
          if (!old) return old;
          return {
            ...old,
            notifications: old.notifications.map((n: Notification) =>
              n.id === notificationId
                ? { ...n, read_at: new Date().toISOString() }
                : n
            ),
          };
        }
      );

      // Optimistically decrement unread count
      queryClient.setQueryData(
        ['notifications', 'unreadCount'],
        (old: number | undefined) => Math.max(0, (old ?? 0) - 1)
      );

      return { previousData };
    },
    onError: (_err, _notificationId, context) => {
      // Rollback on error
      if (context?.previousData) {
        queryClient.setQueryData(['notifications', queryParams], context.previousData);
      }
    },
    onSettled: () => {
      // Refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: ['notifications', 'unreadCount'] });
    },
  });

  // Mark all notifications as read
  const markAllAsReadMutation = useMutation({
    mutationFn: markAllNotificationsRead,
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: ['notifications'] });

      const previousData = queryClient.getQueryData(['notifications', queryParams]);

      // Optimistically mark all as read
      queryClient.setQueryData(
        ['notifications', queryParams],
        (old: typeof data) => {
          if (!old) return old;
          return {
            ...old,
            notifications: old.notifications.map((n: Notification) => ({
              ...n,
              read_at: n.read_at || new Date().toISOString(),
            })),
          };
        }
      );

      // Set unread count to 0
      queryClient.setQueryData(['notifications', 'unreadCount'], 0);

      return { previousData };
    },
    onError: (_err, _vars, context) => {
      if (context?.previousData) {
        queryClient.setQueryData(['notifications', queryParams], context.previousData);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  // Mark batch of notifications as read
  const markBatchAsReadMutation = useMutation({
    mutationFn: markNotificationsBatchRead,
    onMutate: async (notificationIds) => {
      await queryClient.cancelQueries({ queryKey: ['notifications'] });

      const previousData = queryClient.getQueryData(['notifications', queryParams]);
      const idSet = new Set(notificationIds);

      // Optimistically mark batch as read
      queryClient.setQueryData(
        ['notifications', queryParams],
        (old: typeof data) => {
          if (!old) return old;
          return {
            ...old,
            notifications: old.notifications.map((n: Notification) =>
              idSet.has(n.id)
                ? { ...n, read_at: n.read_at || new Date().toISOString() }
                : n
            ),
          };
        }
      );

      // Decrement unread count by number of actually unread items
      const unreadInBatch =
        data?.notifications.filter(
          (n) => idSet.has(n.id) && !n.read_at
        ).length ?? 0;

      queryClient.setQueryData(
        ['notifications', 'unreadCount'],
        (old: number | undefined) => Math.max(0, (old ?? 0) - unreadInBatch)
      );

      return { previousData };
    },
    onError: (_err, _vars, context) => {
      if (context?.previousData) {
        queryClient.setQueryData(['notifications', queryParams], context.previousData);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications', 'unreadCount'] });
    },
  });

  // Action handlers
  const markAsRead = useCallback(
    async (notificationId: string) => {
      await markAsReadMutation.mutateAsync(notificationId);
    },
    [markAsReadMutation]
  );

  const markAllAsRead = useCallback(async () => {
    await markAllAsReadMutation.mutateAsync();
  }, [markAllAsReadMutation]);

  const markBatchAsRead = useCallback(
    async (notificationIds: string[]) => {
      await markBatchAsReadMutation.mutateAsync(notificationIds);
    },
    [markBatchAsReadMutation]
  );

  const refetch = useCallback(async () => {
    await refetchList();
  }, [refetchList]);

  return {
    notifications: data?.notifications ?? [],
    total: data?.total ?? 0,
    unreadCount: unreadCountData ?? 0,
    isLoading,
    isError,
    error: error as Error | null,
    markAsRead,
    markAllAsRead,
    markBatchAsRead,
    refetch,
    page,
    pageSize,
    hasMore: (data?.total ?? 0) > page * pageSize,
  };
}

export { useNotifications as default };
