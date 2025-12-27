/**
 * API Service for Werewolf Game Backend
 * Handles all HTTP requests to the FastAPI backend
 */

// Use empty string for relative URLs (nginx proxy), or explicit URL for direct access
const API_BASE_URL = import.meta.env.VITE_API_URL !== undefined
  ? import.meta.env.VITE_API_URL
  : 'http://localhost:8000';

// Types matching backend schemas
export type Role = 'werewolf' | 'villager' | 'seer' | 'witch' | 'hunter';
export type GameStatus = 'waiting' | 'playing' | 'finished';
export type GamePhase =
  | 'night_start'
  | 'night_werewolf_chat'
  | 'night_werewolf'
  | 'night_seer'
  | 'night_witch'
  | 'day_announcement'
  | 'day_last_words'
  | 'day_speech'
  | 'day_vote'
  | 'day_vote_result'
  | 'hunter_shoot'
  | 'game_over';
export type ActionType = 'kill' | 'verify' | 'save' | 'poison' | 'vote' | 'shoot' | 'speak' | 'skip';
export type MessageType = 'speech' | 'system' | 'thought' | 'last_words';
export type Winner = 'werewolf' | 'villager' | 'none';

export interface PlayerPublic {
  seat_id: number;
  is_alive: boolean;
  is_human: boolean;
  avatar?: string | null;
  name?: string | null;
  role?: Role | null; // only shown when game is finished
}

export interface MessageInGame {
  seat_id: number;
  text: string;
  type: MessageType;
  day: number;
}

export interface PendingAction {
  type: ActionType;
  choices: number[];
  message?: string | null;
}

export interface GameState {
  game_id: string;
  status: GameStatus;
  day: number;
  phase: GamePhase;
  current_actor?: number | null;
  my_seat: number;
  my_role: Role;
  players: PlayerPublic[];
  message_log: MessageInGame[];
  pending_action?: PendingAction | null;
  winner?: Winner | null;
  night_kill_target?: number | null;
  wolf_teammates: number[];
  verified_results: Record<number, boolean>;
  wolf_votes_visible?: Record<number, number>; // teammate_seat -> target_seat
}

export interface GameStartRequest {
  human_seat?: number | null;
  human_role?: Role | null;
  language?: string;  // Game language: "zh" or "en"
}

export interface GameStartResponse {
  game_id: string;
  player_role: Role;
  player_seat: number;
  players: PlayerPublic[];
}

export interface StepResponse {
  status: string;
  new_phase?: GamePhase | null;
  message?: string | null;
}

export interface ActionRequest {
  seat_id: number;
  action_type: ActionType;
  target_id?: number | null;
  content?: string | null;
}

export interface ActionResponse {
  success: boolean;
  message?: string | null;
}

// API Error class
export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string
  ) {
    super(detail);
    this.name = 'ApiError';
  }
}

// Generic fetch wrapper with error handling
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  };

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  if (!response.ok) {
    let detail = 'Unknown error';
    try {
      const errorData = await response.json();
      detail = errorData.detail || errorData.message || JSON.stringify(errorData);
    } catch {
      detail = response.statusText;
    }
    throw new ApiError(response.status, detail);
  }

  return response.json();
}

// ==================== Game API ====================

/**
 * Start a new game
 */
export async function startGame(request: GameStartRequest = {}): Promise<GameStartResponse> {
  // Auto-detect current language if not provided
  if (!request.language) {
    request.language = i18n.language || 'zh';
  }

  return fetchApi<GameStartResponse>('/api/game/start', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Get current game state
 */
export async function getGameState(gameId: string): Promise<GameState> {
  return fetchApi<GameState>(`/api/game/${gameId}/state`);
}

/**
 * Advance game state by one step
 */
export async function stepGame(gameId: string): Promise<StepResponse> {
  return fetchApi<StepResponse>(`/api/game/${gameId}/step`, {
    method: 'POST',
  });
}

/**
 * Submit a player action
 */
export async function submitAction(
  gameId: string,
  action: ActionRequest
): Promise<ActionResponse> {
  return fetchApi<ActionResponse>(`/api/game/${gameId}/action`, {
    method: 'POST',
    body: JSON.stringify(action),
  });
}

/**
 * Delete a game
 */
export async function deleteGame(gameId: string): Promise<{ success: boolean; message: string }> {
  return fetchApi(`/api/game/${gameId}`, {
    method: 'DELETE',
  });
}

/**
 * Health check
 */
export async function healthCheck(): Promise<{ status: string }> {
  return fetchApi('/health');
}

// ==================== Helper Functions ====================

import i18n from '@/i18n/config';

/**
 * Get role display name (i18n-aware)
 */
export function getRoleDisplayName(role: Role): string {
  return i18n.t(`roles:${role}`);
}

/**
 * Get phase display name (i18n-aware)
 */
export function getPhaseDisplayName(phase: GamePhase): string {
  return i18n.t(`game:phase.${phase}`);
}

/**
 * Check if current phase is night
 */
export function isNightPhase(phase: GamePhase): boolean {
  return phase.startsWith('night_');
}

/**
 * Check if human player needs to act
 */
export function needsHumanAction(gameState: GameState): boolean {
  return gameState.pending_action !== null && gameState.pending_action !== undefined;
}
