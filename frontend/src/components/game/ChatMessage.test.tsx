/**
 * ChatMessage Security Tests
 *
 * T-06: Verifies XSS protection in chat components.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: 'en' },
  }),
}));

// Mock vote utils
vi.mock('@/utils/voteUtils', () => ({
  isVoteResultMessage: () => false,
  parseVoteResult: () => null,
}));

import ChatMessage from './ChatMessage';

describe('ChatMessage Security', () => {
  it('escapes HTML entities in message content', () => {
    const xssPayload = '<script>alert("xss")</script>';

    render(
      <ChatMessage
        sender="Player 1"
        message={xssPayload}
        isUser={false}
        timestamp="12:00"
      />
    );

    // The script tag should be rendered as text, not executed
    expect(screen.getByText(xssPayload)).toBeInTheDocument();

    // Verify no script elements were created
    const scripts = document.querySelectorAll('script');
    expect(scripts.length).toBe(0);
  });

  it('escapes HTML entities in sender name', () => {
    const xssPayload = '<img src=x onerror="alert(1)">';

    render(
      <ChatMessage
        sender={xssPayload}
        message="Hello"
        isUser={false}
        timestamp="12:00"
      />
    );

    // The malicious img tag should be rendered as text
    expect(screen.getByText(xssPayload)).toBeInTheDocument();

    // Verify no img elements with the malicious src were created
    const images = document.querySelectorAll('img[src="x"]');
    expect(images.length).toBe(0);
  });

  it('renders system messages safely', () => {
    const xssPayload = '<div onmouseover="alert(1)">hover me</div>';

    render(
      <ChatMessage
        sender="System"
        message={xssPayload}
        isUser={false}
        isSystem={true}
        timestamp="12:00"
      />
    );

    // The div tag should be rendered as text
    expect(screen.getByText(xssPayload)).toBeInTheDocument();
  });

  it('handles special characters safely', () => {
    const specialChars = '&lt;script&gt; &amp; &quot;test&quot;';

    render(
      <ChatMessage
        sender="Player"
        message={specialChars}
        isUser={false}
        timestamp="12:00"
      />
    );

    // Special characters should be preserved as-is
    expect(screen.getByText(specialChars)).toBeInTheDocument();
  });
});
