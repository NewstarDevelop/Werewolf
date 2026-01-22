/**
 * Hook for fetching game replay data
 */

import { useQuery } from '@tanstack/react-query';
import { getGameReplay, type GameReplayResponse } from '@/services/gameHistoryApi';

export function useGameReplay(gameId: string | undefined) {
  return useQuery<GameReplayResponse>({
    queryKey: ['gameReplay', gameId],
    queryFn: () => {
      if (!gameId) {
        throw new Error('Game ID is required');
      }
      return getGameReplay(gameId);
    },
    enabled: !!gameId,
    staleTime: 5 * 60 * 1000, // 5 minutes - replay data doesn't change
    retry: 1,
  });
}
