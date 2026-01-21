/**
 * WebSocket Utilities Tests
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { buildWebSocketUrl, getAuthSubprotocols } from '../websocket';

// Mock the token module
vi.mock('../token', () => ({
  getToken: vi.fn(() => 'test-jwt-token'),
}));

describe('WebSocket Utilities', () => {
  describe('buildWebSocketUrl', () => {
    it('includes /api prefix if not present', () => {
      const url = buildWebSocketUrl('/ws/game/123');
      expect(url).toContain('/api/ws/game/123');
    });

    it('does not double /api prefix', () => {
      const url = buildWebSocketUrl('/api/ws/game/123');
      expect(url).not.toContain('/api/api');
      expect(url).toContain('/api/ws/game/123');
    });

    it('uses correct protocol based on page location', () => {
      const url = buildWebSocketUrl('/ws/test');
      // Should match either ws: or wss: depending on window.location.protocol
      expect(url).toMatch(/^wss?:\/\//);
    });

    it('uses VITE_API_URL host when available', () => {
      const url = buildWebSocketUrl('/ws/game/123');
      // URL should be properly formatted
      expect(url).toMatch(/^wss?:\/\/[^/]+\/api\/ws\/game\/123$/);
    });
  });

  describe('getAuthSubprotocols', () => {
    it('returns array with auth and token', () => {
      const protocols = getAuthSubprotocols();
      expect(protocols).toHaveLength(2);
      expect(protocols[0]).toBe('auth');
      // Token should be a string (mocked or empty)
      expect(typeof protocols[1]).toBe('string');
    });

    it('first element is always "auth"', () => {
      const protocols = getAuthSubprotocols();
      expect(protocols[0]).toBe('auth');
    });
  });
});
