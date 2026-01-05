import { useRef, useEffect, useCallback } from "react";
import { FixedSizeList, ListOnScrollProps } from "react-window";
import { AutoSizer } from "react-virtualized-auto-sizer";
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
  const listRef = useRef<FixedSizeList>(null);
  const isNearBottomRef = useRef(true);
  const { t } = useTranslation('common');

  const shouldVirtualize = messages.length > 50;

  // Track scroll position for virtualized list
  const handleVirtualScroll = useCallback(({ scrollOffset, scrollDirection }: ListOnScrollProps) => {
    if (!listRef.current) return;
    const listHeight = (listRef.current.props as { height: number }).height;
    const totalHeight = messages.length * 80;
    const isNearBottom = totalHeight - scrollOffset - listHeight < 100;
    isNearBottomRef.current = isNearBottom;
  }, [messages.length]);

  // P2-3: Smart scroll - only auto-scroll if user is near bottom
  useEffect(() => {
    if (shouldVirtualize && listRef.current) {
      // Only auto-scroll if user is near bottom
      if (isNearBottomRef.current) {
        listRef.current.scrollToItem(messages.length - 1, "end");
      }
    } else if (scrollRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;

      // Only auto-scroll if user is near bottom (within 100px)
      if (isNearBottom) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      }
    }
  }, [messages, shouldVirtualize]);

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
      {messages.length === 0 ? (
        <div className="flex items-center justify-center flex-1 text-muted-foreground text-sm">
          {t('player.waiting')}
        </div>
      ) : shouldVirtualize ? (
        <div className="flex-1">
          <AutoSizer>
            {({ height, width }) => (
              <FixedSizeList
                ref={listRef}
                height={height}
                width={width}
                itemCount={messages.length}
                itemSize={80}
                onScroll={handleVirtualScroll}
                className="p-4 scrollbar-thin"
              >
                {({ index, style }) => {
                  const msg = messages[index];
                  return (
                    <div style={style}>
                      <ChatMessage
                        sender={msg.sender}
                        message={msg.message}
                        isUser={msg.isUser}
                        isSystem={msg.isSystem}
                        timestamp={msg.timestamp}
                        day={msg.day}
                      />
                    </div>
                  );
                }}
              </FixedSizeList>
            )}
          </AutoSizer>
        </div>
      ) : (
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto p-4 scrollbar-thin"
        >
          {messages.map((msg) => (
            <ChatMessage
              key={msg.id}
              sender={msg.sender}
              message={msg.message}
              isUser={msg.isUser}
              isSystem={msg.isSystem}
              timestamp={msg.timestamp}
              day={msg.day}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default ChatLog;
