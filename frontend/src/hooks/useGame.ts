/**
 * useGame Hook - Manages game state and API interactions
 */
import { useState, useCallback, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  startGame,
  getGameState,
  stepGame,
  submitAction,
  GameState,
  GameStartResponse,
  StepResponse,
  ActionType,
  Role,
  isNightPhase,
  needsHumanAction,
} from '@/services/api';

interface UseGameOptions {
  autoStep?: boolean;
  stepInterval?: number;
}

export function useGame(options: UseGameOptions = {}) {
  const { autoStep = true, stepInterval = 1500 } = options;

  const [gameId, setGameId] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const stepTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Query for game state
  const {
    data: gameState,
    isLoading: isLoadingState,
    refetch: refetchState,
  } = useQuery({
    queryKey: ['gameState', gameId],
    queryFn: () => (gameId ? getGameState(gameId) : null),
    enabled: !!gameId,
    refetchInterval: false, // We'll manually control refetching
    staleTime: 0,
  });

  // Mutation for starting a new game
  const startGameMutation = useMutation({
    mutationFn: startGame,
    onSuccess: (data: GameStartResponse) => {
      setGameId(data.game_id);
      setError(null);
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  // Mutation for stepping the game
  const stepGameMutation = useMutation({
    mutationFn: () => (gameId ? stepGame(gameId) : Promise.reject('No game')),
    onSuccess: async (data: StepResponse) => {
      // Refetch state after step
      await refetchState();

      // If game is still running and not waiting for human, schedule next step
      if (autoStep && data.status === 'updated') {
        scheduleNextStep();
      }
    },
    onError: (err: Error) => {
      console.error('Step error:', err);
    },
  });

  // Mutation for submitting actions
  const submitActionMutation = useMutation({
    mutationFn: ({
      actionType,
      targetId,
      content,
    }: {
      actionType: ActionType;
      targetId?: number | null;
      content?: string | null;
    }) => {
      if (!gameId || !gameState) return Promise.reject('No game');
      return submitAction(gameId, {
        seat_id: gameState.my_seat,
        action_type: actionType,
        target_id: targetId,
        content: content,
      });
    },
    onSuccess: async () => {
      // CRITICAL FIX: Wait for state to update before scheduling next step
      // This prevents race conditions in witch two-phase decision (save -> poison)
      await refetchState();

      // Add a small delay to ensure React query cache is updated
      await new Promise(resolve => setTimeout(resolve, 100));

      if (autoStep) {
        scheduleNextStep();
      }
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  // Schedule next step with delay
  const scheduleNextStep = useCallback(() => {
    if (stepTimeoutRef.current) {
      clearTimeout(stepTimeoutRef.current);
    }
    stepTimeoutRef.current = setTimeout(() => {
      stepGameMutation.mutate();
    }, stepInterval);
  }, [stepInterval, stepGameMutation]);

  // Start a new game
  const handleStartGame = useCallback(
    async (humanSeat?: number, humanRole?: Role) => {
      setIsStarting(true);
      setError(null);
      try {
        await startGameMutation.mutateAsync({
          human_seat: humanSeat,
          human_role: humanRole,
        });
      } finally {
        setIsStarting(false);
      }
    },
    [startGameMutation]
  );

  // Manually trigger a step
  const handleStep = useCallback(() => {
    if (gameId) {
      stepGameMutation.mutate();
    }
  }, [gameId, stepGameMutation]);

  // Submit player action
  const handleAction = useCallback(
    async (actionType: ActionType, targetId?: number | null, content?: string | null) => {
      await submitActionMutation.mutateAsync({ actionType, targetId, content });
    },
    [submitActionMutation]
  );

  // Convenience methods for specific actions
  const handleSpeak = useCallback(
    (content: string) => handleAction('speak', null, content),
    [handleAction]
  );

  const handleVote = useCallback(
    (targetId: number | null) => handleAction('vote', targetId),
    [handleAction]
  );

  const handleKill = useCallback(
    (targetId: number) => handleAction('kill', targetId),
    [handleAction]
  );

  const handleVerify = useCallback(
    (targetId: number) => handleAction('verify', targetId),
    [handleAction]
  );

  const handleSave = useCallback(() => handleAction('save'), [handleAction]);

  const handlePoison = useCallback(
    (targetId: number) => handleAction('poison', targetId),
    [handleAction]
  );

  const handleShoot = useCallback(
    (targetId: number | null) => handleAction('shoot', targetId),
    [handleAction]
  );

  const handleSkip = useCallback(() => handleAction('skip'), [handleAction]);

  // Auto-step when game starts or state changes
  useEffect(() => {
    if (gameId && gameState && autoStep) {
      const needsAction = needsHumanAction(gameState);
      const isGameOver = gameState.status === 'finished';

      if (!needsAction && !isGameOver && !stepGameMutation.isPending) {
        scheduleNextStep();
      }
    }

    return () => {
      if (stepTimeoutRef.current) {
        clearTimeout(stepTimeoutRef.current);
      }
    };
  }, [gameId, gameState, autoStep, scheduleNextStep, stepGameMutation.isPending]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (stepTimeoutRef.current) {
        clearTimeout(stepTimeoutRef.current);
      }
    };
  }, []);

  // Derived state
  const isNight = gameState ? isNightPhase(gameState.phase) : false;
  const needsAction = gameState ? needsHumanAction(gameState) : false;
  const isGameOver = gameState?.status === 'finished';
  const isLoading = isStarting || isLoadingState || stepGameMutation.isPending;

  return {
    // State
    gameId,
    gameState,
    isLoading,
    isStarting,
    error,
    isNight,
    needsAction,
    isGameOver,

    // Actions
    startGame: handleStartGame,
    step: handleStep,
    speak: handleSpeak,
    vote: handleVote,
    kill: handleKill,
    verify: handleVerify,
    save: handleSave,
    poison: handlePoison,
    shoot: handleShoot,
    skip: handleSkip,
    submitAction: handleAction,

    // Mutations state
    isSubmitting: submitActionMutation.isPending,
    isStepping: stepGameMutation.isPending,
  };
}

export default useGame;
