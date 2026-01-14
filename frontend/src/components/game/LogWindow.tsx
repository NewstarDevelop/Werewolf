import { useEffect, useRef } from 'react';
import { Message } from '@/types/game';
import { useTranslation } from 'react-i18next';

export default function LogWindow({ messages }: { messages: Message[] }) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const { t } = useTranslation('common');

  useEffect(() => {
    // 自动滚动到底部
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="h-96 overflow-y-auto bg-card p-4 rounded-lg border border-border">
      {messages.map((msg, idx) => (
        <div key={idx} className={`mb-3 ${msg.seat_id === 0 ? 'text-center text-amber-700 dark:text-yellow-500 text-sm' : ''}`}>
          {msg.seat_id !== 0 && (
            <span className="font-bold text-blue-700 dark:text-blue-500 mr-2">
              {t('player.seat_with_id', { id: msg.seat_id })}:
            </span>
          )}
          <span className="text-card-foreground">{msg.content}</span>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
