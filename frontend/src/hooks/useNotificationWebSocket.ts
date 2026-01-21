/**
 * useNotificationWebSocket Hook - Real-time notification updates via WebSocket
 *
 * Features:
 * - Global WebSocket connection to /ws/notifications
 * - Authentication via HttpOnly cookie (automatic)
 * - Automatic reconnection with exponential backoff
 * - Integration with TanStack Query cache
 * - Toast notifications via Sonner
 */
import { useEffect, useRef, useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import type {
  Notification,
  NotificationWSMessage,
  NotificationCategory,
} from '@/types/notification';

interface UseNotificationWebSocketOptions {
  enabled?: boolean;
  onError?: (error: Error) => void;
  onNotification?: (notification: Notification) => void;
}

interface UseNotificationWebSocketReturn {
  isConnected: boolean;
  connectionError: string | null;
  unreadCount: number;
  reconnect: () => void;
}

// Category display info
const CATEGORY_INFO: Record<
  NotificationCategory,
  { icon: string; color: string }
> = {
  GAME: { icon: '🎮', color: 'blue' },
  ROOM: { icon: '🚪', color: 'green' },
  SOCIAL: { icon: '👥', color: 'purple' },
  SYSTEM: { icon: '🔔', color: 'orange' },
};

export function useNotificationWebSocket(
  options: UseNotificationWebSocketOptions = {}
): UseNotificationWebSocketReturn {
  const { enabled = true, onError, onNotification } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const queryClient = useQueryClient();
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const pingIntervalRef = useRef<NodeJS.Timeout>();
  const shouldReconnectRef = useRef(false);
  const onErrorRef = useRef(onError);
  const onNotificationRef = useRef(onNotification);

  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);

  // Keep refs updated
  useEffect(() => {
    onErrorRef.current = onError;
    onNotificationRef.current = onNotification;
  });

  // Handle incoming notification
  const handleNotification = useCallback(
    (notification: Notification) => {
      // Update query cache - prepend new notification
      queryClient.setQueryData(
        ['notifications'],
        (oldData: { notifications: Notification[] } | undefined) => {
          if (!oldData) return { notifications: [notification] };
          return {
            ...oldData,
            notifications: [notification, ...oldData.notifications],
          };
        }
      );

      // Increment unread count
      setUnreadCount((prev) => prev + 1);

      // Show toast notification
      const categoryInfo = CATEGORY_INFO[notification.category] || {
        icon: '🔔',
        color: 'gray',
      };
      toast(notification.title, {
        description: notification.body,
        icon: categoryInfo.icon,
        duration: 5000,
      });

      // Call user callback
      if (onNotificationRef.current) {
        onNotificationRef.current(notification);
      }
    },
    [queryClient]
  );

  // Cleanup function
  const cleanup = useCallback(() => {
    shouldReconnectRef.current = false;
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  // Send ping to keep connection alive
  const sendPing = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send('ping');
      } catch (error) {
        console.error('[NotificationWS] Failed to send ping:', error);
      }
    }
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!enabled) return;

    cleanup();

    try {
      // Determine WebSocket URL based on environment
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = import.meta.env.VITE_API_URL
        ? new URL(import.meta.env.VITE_API_URL).host
        : window.location.host;

      const wsUrl = `${protocol}//${host}/api/ws/notifications`;

      console.log('[NotificationWS] Connecting to:', wsUrl);

      // Authentication is handled via HttpOnly cookie (user_access_token)
      // No need to pass token via Sec-WebSocket-Protocol
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      shouldReconnectRef.current = true;

      ws.onopen = () => {
        console.log('[NotificationWS] Connected');
        setIsConnected(true);
        setConnectionError(null);

        // Start ping interval to keep connection alive
        pingIntervalRef.current = setInterval(sendPing, 30000);
      };

      ws.onmessage = (event) => {
        try {
          if (event.data === 'pong') return;

          const message: NotificationWSMessage = JSON.parse(event.data);
          console.log('[NotificationWS] Received:', message.type);

          switch (message.type) {
            case 'connected':
              // Initial connection - set unread count
              if (typeof message.data.unread_count === 'number') {
                setUnreadCount(message.data.unread_count);
              }
              break;

            case 'notification':
              // New notification received
              if (message.data.notification) {
                handleNotification(message.data.notification);
              }
              break;

            case 'error':
              console.error('[NotificationWS] Server error:', message.data);
              setConnectionError('Server error');
              if (onErrorRef.current) {
                onErrorRef.current(new Error('Server error'));
              }
              break;

            case 'pong':
              // Heartbeat response, ignore
              break;
          }
        } catch (error) {
          console.error('[NotificationWS] Failed to parse message:', error);
        }
      };

      ws.onerror = (event) => {
        console.error('[NotificationWS] Error:', event);
        setConnectionError('WebSocket connection error');
        if (onErrorRef.current) {
          onErrorRef.current(new Error('WebSocket connection error'));
        }
      };

      ws.onclose = (event) => {
        console.log('[NotificationWS] Disconnected:', event.code, event.reason);
        setIsConnected(false);

        // Reconnect with backoff (unless intentionally closed or auth error)
        if (
          event.code !== 1000 &&
          event.code !== 1008 &&
          enabled &&
          shouldReconnectRef.current
        ) {
          console.log('[NotificationWS] Reconnecting in 3 seconds...');
          reconnectTimeoutRef.current = setTimeout(connect, 3000);
        }
      };
    } catch (error) {
      console.error('[NotificationWS] Connection failed:', error);
      setConnectionError('Failed to establish WebSocket connection');
      if (onErrorRef.current) {
        onErrorRef.current(error as Error);
      }

      // Retry connection after delay
      if (enabled && shouldReconnectRef.current) {
        reconnectTimeoutRef.current = setTimeout(connect, 5000);
      }
    }
  }, [enabled, cleanup, sendPing, handleNotification]);

  // Connect on mount when enabled
  useEffect(() => {
    if (enabled) {
      connect();
    }

    return cleanup;
  }, [enabled]); // Intentionally minimal deps to avoid infinite reconnects

  // Method to manually update unread count (e.g., after marking as read)
  const updateUnreadCount = useCallback((count: number) => {
    setUnreadCount(count);
  }, []);

  return {
    isConnected,
    connectionError,
    unreadCount,
    reconnect: connect,
  };
}

export { useNotificationWebSocket as default };
