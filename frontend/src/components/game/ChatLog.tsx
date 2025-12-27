import { useRef, useEffect } from "react";
import ChatMessage from "./ChatMessage";
import { MessageCircle, Loader2 } from "lucide-react";
import { useTranslation } from "react-i18next";

interface Message {
  id: number;
  sender: string;
  message: string;
  isUser: boolean;
  isSystem?: boolean;
  timestamp: string;
  day?: number;
}

interface ChatLogProps {
  messages: Message[];
  isLoading?: boolean;
}

const ChatLog = ({ messages, isLoading }: ChatLogProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const { t } = useTranslation('common');

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="flex flex-col h-full bg-card/50 rounded-xl border border-border overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border bg-muted/30">
        <MessageCircle className="w-4 h-4 text-accent" />
        <h2 className="font-display text-sm uppercase tracking-wider text-foreground">
          {t('ui.game_log')}
        </h2>
        <span className="ml-auto text-xs text-muted-foreground">
          {t('player.messages_count', { count: messages.length })}
        </span>
        {isLoading && (
          <Loader2 className="w-4 h-4 text-accent animate-spin" />
        )}
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 scrollbar-thin"
      >
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
            {t('player.waiting')}
          </div>
        ) : (
          messages.map((msg) => (
            <ChatMessage
              key={msg.id}
              sender={msg.sender}
              message={msg.message}
              isUser={msg.isUser}
              isSystem={msg.isSystem}
              timestamp={msg.timestamp}
              day={msg.day}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default ChatLog;
