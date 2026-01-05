import { useRef, useEffect, useCallback, useState } from "react";
import { VariableSizeList, ListOnScrollProps } from "react-window";
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

// 估算消息高度：系统消息较短，普通消息较高
const getItemSize = (msg: Message): number => {
  if (msg.isSystem) return 52; // 系统消息：padding + 单行
  // 普通消息：发送者行 + 消息气泡 + margin
  const baseHeight = 72;
  // 长消息额外增加高度（每50字符约增加一行）
  const extraLines = Math.floor(msg.message.length / 50);
  return baseHeight + extraLines * 20;
};

const ChatLog = ({ messages, isLoading }: ChatLogProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<VariableSizeList>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const isNearBottomRef = useRef(true);
  const { t } = useTranslation('common');
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });

  const shouldVirtualize = messages.length > 50;

  // 监听容器尺寸变化
  useEffect(() => {
    if (!containerRef.current) return;
    const resizeObserver = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) {
        setContainerSize({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });
    resizeObserver.observe(containerRef.current);
    return () => resizeObserver.disconnect();
  }, []);

  // 消息变化时重置缓存的高度
  useEffect(() => {
    if (listRef.current) {
      listRef.current.resetAfterIndex(0);
    }
  }, [messages]);

  // Track scroll position for virtualized list
  const handleVirtualScroll = useCallback(({ scrollOffset }: ListOnScrollProps) => {
    if (!listRef.current || containerSize.height === 0) return;
    // 计算总高度
    let totalHeight = 0;
    for (let i = 0; i < messages.length; i++) {
      totalHeight += getItemSize(messages[i]);
    }
    const isNearBottom = totalHeight - scrollOffset - containerSize.height < 100;
    isNearBottomRef.current = isNearBottom;
  }, [messages, containerSize.height]);

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
        <div ref={containerRef} className="flex-1 min-h-0">
          {containerSize.height > 0 && containerSize.width > 0 && (
            <VariableSizeList
              ref={listRef}
              height={containerSize.height}
              width={containerSize.width}
              itemCount={messages.length}
              itemSize={(index) => getItemSize(messages[index])}
              onScroll={handleVirtualScroll}
              className="scrollbar-thin"
              style={{ padding: '16px' }}
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
            </VariableSizeList>
          )}
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
