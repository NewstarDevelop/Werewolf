/**
 * Token Management Utilities
 *
 * TOKEN ARCHITECTURE (2026-01-21):
 *
 * 1. USER AUTHENTICATION
 *    - Uses HttpOnly cookies set by backend (/auth/login)
 *    - All API calls include credentials: 'include'
 *    - No client-side token storage for user auth
 *
 * 2. GAME ROOM AUTHENTICATION
 *    - Uses JWT stored in sessionStorage
 *    - Token issued when joining/creating room
 *    - Passed via Authorization header for game-related APIs
 *    - Also used for WebSocket Sec-WebSocket-Protocol authentication
 *
 * This dual-auth approach allows:
 * - Secure user sessions via HttpOnly cookies
 * - Game-specific authorization without modifying user session
 */

const TOKEN_KEY = 'werewolf_token';
const EXPIRY_KEY = 'werewolf_token_expiry';
const DEFAULT_EXPIRY_MS = 24 * 60 * 60 * 1000; // 24 hours

/**
 * Save game room JWT token to sessionStorage.
 * @param token - JWT token string
 * @param expiresIn - Expiry time in milliseconds (default 24 hours)
 */
export function saveToken(token: string, expiresIn: number = DEFAULT_EXPIRY_MS): void {
  if (!token) {
    console.warn('[Token] Attempted to save empty token');
    return;
  }
  const expiryTime = Date.now() + expiresIn;
  sessionStorage.setItem(TOKEN_KEY, token);
  sessionStorage.setItem(EXPIRY_KEY, expiryTime.toString());
}

/**
 * Get game room JWT token from sessionStorage.
 * Returns null if token doesn't exist or has expired.
 */
export function getToken(): string | null {
  const token = sessionStorage.getItem(TOKEN_KEY);
  const expiry = sessionStorage.getItem(EXPIRY_KEY);

  if (!token || !expiry) return null;

  if (Date.now() > parseInt(expiry, 10)) {
    clearToken();
    return null;
  }

  return token;
}

/**
 * Clear stored game room token.
 */
export function clearToken(): void {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(EXPIRY_KEY);
}

/**
 * Get Authorization header for game room authentication.
 * Used by API calls that require game room context.
 * @returns Headers object with Authorization or empty object if no token
 */
export function getAuthHeader(): HeadersInit {
  const token = getToken();
  if (!token) {
    return {};
  }
  return {
    'Authorization': `Bearer ${token}`
  };
}

// =============================================================================
// LEGACY CLEANUP FUNCTIONS
// These exist only for backward compatibility cleanup during logout
// =============================================================================

const USER_TOKEN_KEY = 'user_auth_token';

/**
 * Clear any legacy user token from localStorage.
 * Called during logout to ensure clean state.
 */
export function clearUserToken(): void {
  localStorage.removeItem(USER_TOKEN_KEY);
}
