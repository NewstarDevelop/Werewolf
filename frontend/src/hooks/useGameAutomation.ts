import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { GameState, needsHumanAction } from '@/services/api';

interface UseGameAutomationOptions {
  gameId: string | null;
  gameState?: GameState | null;
  autoStep: boolean;
  stepInterval: number;
  stepErrorCount: number;
  stepMutateRef: React.MutableRefObject<((variables?: void) => void) | null>;
  isStepping: boolean;
}

export function useGameAutomation({
  gameId,
  gameState,
  autoStep,
  stepInterval,
  stepErrorCount,
  stepMutateRef,
  isStepping
}: UseGameAutomationOptions) {
  const queryClient = useQueryClient();
  const stepTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const MAX_STEP_ERRORS = 3;
  const isAutoStepPaused = stepErrorCount >= MAX_STEP_ERRORS;

  // Fix #7: Include stepMutateRef in dependencies to satisfy exhaustive-deps
  const scheduleNextStep = useCallback(() => {
    if (stepTimeoutRef.current) clearTimeout(stepTimeoutRef.current);
    stepTimeoutRef.current = setTimeout(() => {
      const currentGameState = queryClient.getQueryData<GameState>(['gameState', gameId]);
      if (!currentGameState) return;
      if (!needsHumanAction(currentGameState) && currentGameState.status !== 'finished') {
        stepMutateRef.current?.();
      }
    }, stepInterval);
  }, [stepInterval, queryClient, gameId, stepMutateRef]);

  useEffect(() => {
    if (gameId && gameState && autoStep && !needsHumanAction(gameState) && gameState.status !== 'finished' && !isStepping && !isAutoStepPaused) {
      scheduleNextStep();
    }
    return () => { if (stepTimeoutRef.current) clearTimeout(stepTimeoutRef.current); };
  }, [gameId, gameState, autoStep, scheduleNextStep, isStepping, isAutoStepPaused]);

  return { isAutoStepPaused };
}
