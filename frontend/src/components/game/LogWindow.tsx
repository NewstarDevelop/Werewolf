import { useEffect, useRef } from 'react';
import { Message } from '@/types/game';

export default function LogWindow({ messages }: { messages: Message[] }) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // 自动滚动到底部
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="h-96 overflow-y-auto bg-gray-800 p-4 rounded-lg border border-gray-700">
      {messages.map((msg, idx) => (
        <div key={idx} className={`mb-3 ${msg.seat_id === 0 ? 'text-center text-yellow-400 text-sm' : ''}`}>
          {msg.seat_id !== 0 && (
            <span className="font-bold text-blue-400 mr-2">
              {msg.seat_id}号:
            </span>
          )}
          <span className="text-gray-200">{msg.content}</span>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
