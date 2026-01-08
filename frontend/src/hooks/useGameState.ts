import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { getGameState, GameState } from '@/services/api';
import { useGameWebSocket } from './useGameWebSocket';

interface UseGameStateOptions {
  gameId?: string | null;
  enableWebSocket?: boolean;
}

export function useGameState(options: UseGameStateOptions) {
  const { gameId, enableWebSocket = true } = options;
  const [wsReceivedFirstUpdate, setWsReceivedFirstUpdate] = useState(false);

  const { isConnected: isWebSocketConnected, connectionError: wsError } = useGameWebSocket({
    gameId,
    enabled: enableWebSocket && !!gameId,
    onFirstUpdate: () => setWsReceivedFirstUpdate(true),
    onError: (err) => {
      console.warn('[WebSocket] Connection error, falling back to polling:', err.message);
      setWsReceivedFirstUpdate(false);
    },
  });

  const {
    data: gameState,
    isLoading,
    refetch,
    error,
    isError,
  } = useQuery({
    queryKey: ['gameState', gameId],
    queryFn: () => (gameId ? getGameState(gameId) : null),
    enabled: !!gameId,
    refetchInterval: (query) => {
      const state = query.state.data as GameState | null;
      if (state?.status === 'finished') return false;
      const shouldSlowPoll = enableWebSocket && isWebSocketConnected && !wsError && wsReceivedFirstUpdate;
      return shouldSlowPoll ? 10000 : 2000;
    },
    refetchIntervalInBackground: false,
    staleTime: 0,
  });

  return {
    gameState,
    isLoading,
    refetch,
    error,
    isError,
    isWebSocketConnected,
    wsError,
    wsReceivedFirstUpdate,
  };
}
