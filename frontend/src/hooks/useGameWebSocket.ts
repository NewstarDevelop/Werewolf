/**
 * useGameWebSocket Hook - Real-time game state updates via WebSocket
 */
import { useEffect, useRef, useCallback, useState } from 'react';
import { GameState } from '@/services/api';
import { useQueryClient } from '@tanstack/react-query';
import { getToken } from '@/utils/token';

interface UseGameWebSocketOptions {
  gameId: string | null;
  enabled?: boolean;
  onError?: (error: Error) => void;
  onFirstUpdate?: () => void;
}

interface WebSocketMessage {
  type: 'game_update' | 'connected' | 'error' | 'pong';
  data: any;
}

// Message deduplication helper
function mergeMessages(oldMessages: any[], newMessages: any[]): any[] {
  // Server message_log is authoritative; do not dedupe to avoid dropping valid duplicates.
  return Array.isArray(newMessages) ? newMessages : oldMessages;
}

export function useGameWebSocket({ gameId, enabled = true, onError, onFirstUpdate }: UseGameWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const queryClient = useQueryClient();
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const pingIntervalRef = useRef<NodeJS.Timeout>();
  const shouldReconnectRef = useRef(false);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

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
        console.error('Failed to send ping:', error);
      }
    }
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!gameId || !enabled) return;

    cleanup();

    try {
      // Determine WebSocket URL based on environment
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = import.meta.env.VITE_API_URL
        ? new URL(import.meta.env.VITE_API_URL).host
        : window.location.host;
      const wsUrl = `${protocol}//${host}/api/ws/game/${gameId}?token=${encodeURIComponent(getToken() || '')}`;

      console.log('[WebSocket] Connecting to:', wsUrl);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      shouldReconnectRef.current = true;

      ws.onopen = () => {
        console.log('[WebSocket] Connected to game', gameId);
        setIsConnected(true);
        setConnectionError(null);

        // Start ping interval to keep connection alive
        pingIntervalRef.current = setInterval(sendPing, 30000); // Ping every 30s
      };

      ws.onmessage = (event) => {
        try {
          if (event.data === 'pong') return;
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('[WebSocket] Received message:', message.type);

          if (message.type === 'game_update') {
            // Intelligent state merging with version control
            queryClient.setQueryData(['gameState', gameId], (old: GameState | undefined) => {
              // Version check: reject stale updates
              if (old && message.data.state_version !== undefined &&
                  old.state_version !== undefined &&
                  message.data.state_version <= old.state_version) {
                console.warn(`[WebSocket] Stale update rejected (v${message.data.state_version} <= v${old.state_version})`);
                return old;
              }

              // Data integrity check
              const isComplete = message.data.message_log && message.data.players;
              if (!isComplete) {
                console.warn('[WebSocket] Incomplete data, triggering refetch');
                queryClient.invalidateQueries({ queryKey: ['gameState', gameId] });
                return old;
              }

              // Merge strategy: preserve old data, overlay new fields
              const merged = {
                ...old,
                ...message.data,
                // Message deduplication and merge
                message_log: mergeMessages(old?.message_log || [], message.data.message_log)
              };

              // Trigger onFirstUpdate callback
              if (onFirstUpdate) {
                onFirstUpdate();
              }

              return merged;
            });
          } else if (message.type === 'connected') {
            // Initial connection: directly set data
            queryClient.setQueryData(['gameState', gameId], message.data);
            if (onFirstUpdate) {
              onFirstUpdate();
            }
          } else if (message.type === 'error') {
            console.error('[WebSocket] Server error:', message.data);
            setConnectionError(message.data.message || 'WebSocket error');
            if (onError) {
              onError(new Error(message.data.message || 'WebSocket error'));
            }
          }
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error);
        }
      };

      ws.onerror = (event) => {
        console.error('[WebSocket] Error:', event);
        setConnectionError('WebSocket connection error');
        if (onError) {
          onError(new Error('WebSocket connection error'));
        }
      };

      ws.onclose = (event) => {
        console.log('[WebSocket] Disconnected:', event.code, event.reason);
        setIsConnected(false);

        // Attempt to reconnect after delay (unless intentionally closed)
        if (event.code !== 1000 && enabled && shouldReconnectRef.current) {
          console.log('[WebSocket] Reconnecting in 3 seconds...');
          reconnectTimeoutRef.current = setTimeout(connect, 3000);
        }
      };
    } catch (error) {
      console.error('[WebSocket] Connection failed:', error);
      setConnectionError('Failed to establish WebSocket connection');
      if (onError) {
        onError(error as Error);
      }

      // Retry connection after delay
      if (enabled && shouldReconnectRef.current) {
        reconnectTimeoutRef.current = setTimeout(connect, 5000);
      }
    }
  }, [gameId, enabled, cleanup, sendPing, queryClient, onError, onFirstUpdate]);

  // Connect on mount and when gameId changes
  useEffect(() => {
    if (gameId && enabled) {
      connect();
    }

    return cleanup;
  }, [gameId, enabled, connect, cleanup]);

  return {
    isConnected,
    connectionError,
    reconnect: connect,
  };
}
