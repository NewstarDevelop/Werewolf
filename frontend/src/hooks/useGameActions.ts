import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useRef, useEffect } from 'react';
import { startGame, stepGame, submitAction, ActionType, Role, GameStartResponse, GameState } from '@/services/api';
import { saveToken } from '@/utils/token';

interface UseGameActionsOptions {
  gameId: string | null;
  gameState?: GameState | null;
  setGameId: (id: string) => void;
  setStepErrorCount: (updater: (prev: number) => number) => void;
  refetchState: () => Promise<any>;
}

export function useGameActions({ gameId, gameState, setGameId, setStepErrorCount, refetchState }: UseGameActionsOptions) {
  const queryClient = useQueryClient();
  const stepMutateRef = useRef<((variables?: void) => void) | null>(null);

  const startGameMutation = useMutation({
    mutationFn: startGame,
    onSuccess: (data: GameStartResponse) => {
      if (data.token) saveToken(data.token);
      setGameId(data.game_id);
      setStepErrorCount(() => 0);
    },
  });

  const stepGameMutation = useMutation({
    mutationFn: () => (gameId ? stepGame(gameId) : Promise.reject(new Error('No game'))),
    onSuccess: async () => {
      try {
        await refetchState();
        setStepErrorCount(() => 0);
      } catch (err) {
        console.error('Refetch error:', err);
        setStepErrorCount(prev => prev + 1);
      }
    },
    onError: (err: Error) => {
      if (err.name === 'AbortError' || err.message?.toLowerCase().includes('aborted')) return;
      console.error('Step error:', err);
      setStepErrorCount(prev => prev + 1);
    },
  });

  // Fix #2: Move ref assignment to useEffect to avoid side effects during render
  useEffect(() => {
    stepMutateRef.current = stepGameMutation.mutate;
  }, [stepGameMutation.mutate]);

  const submitActionMutation = useMutation({
    mutationFn: ({ actionType, targetId, content }: { actionType: ActionType; targetId?: number | null; content?: string | null }) => {
      if (!gameId || !gameState) return Promise.reject(new Error('No game'));
      // Fix #9: Check if my_seat exists to avoid sending undefined
      if (gameState.my_seat === undefined) return Promise.reject(new Error('Player seat not found'));
      return submitAction(gameId, {
        seat_id: gameState.my_seat,
        action_type: actionType,
        target_id: targetId,
        content: content,
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['gameState', gameId] });
    },
  });

  const handleStartGame = useCallback(async (humanSeat?: number, humanRole?: Role) => {
    await startGameMutation.mutateAsync({ human_seat: humanSeat, human_role: humanRole });
  }, [startGameMutation]);

  const handleStep = useCallback(() => {
    if (gameId) stepGameMutation.mutate();
  }, [gameId, stepGameMutation]);

  const handleAction = useCallback(async (actionType: ActionType, targetId?: number | null, content?: string | null) => {
    try {
      await submitActionMutation.mutateAsync({ actionType, targetId, content });
    } catch (err) {
      console.error('Action error:', err);
      throw err;
    }
  }, [submitActionMutation]);

  return {
    startGameMutation,
    stepGameMutation,
    submitActionMutation,
    handleStartGame,
    handleStep,
    handleAction,
    stepMutateRef,
  };
}
