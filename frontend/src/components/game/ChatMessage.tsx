interface ChatMessageProps {
  sender: string;
  message: string;
  isUser: boolean;
  isSystem?: boolean;
  timestamp: string;
  day?: number;
}

const ChatMessage = ({
  sender,
  message,
  isUser,
  isSystem,
  timestamp,
  day,
}: ChatMessageProps) => {
  if (isSystem) {
    return (
      <div className="flex justify-center my-3 animate-slide-up">
        <div className="px-4 py-2 rounded-full bg-accent/10 border border-accent/20 text-accent text-sm">
          {message}
        </div>
      </div>
    );
  }

  return (
    <div
      className={`flex ${
        isUser ? "justify-end" : "justify-start"
      } mb-3 animate-slide-up`}
    >
      <div className={`max-w-[75%] ${isUser ? "order-2" : "order-1"}`}>
        <div
          className={`flex items-center gap-2 mb-1 ${
            isUser ? "justify-end" : "justify-start"
          }`}
        >
          <span
            className={`text-xs font-medium ${
              isUser ? "text-accent" : "text-muted-foreground"
            }`}
          >
            {sender}
          </span>
          {timestamp && (
            <span className="text-xs text-muted-foreground/60">{timestamp}</span>
          )}
        </div>
        <div
          className={`px-4 py-2.5 rounded-2xl ${
            isUser
              ? "bg-accent/20 border border-accent/30 rounded-br-md"
              : "bg-muted border border-border rounded-bl-md"
          }`}
        >
          <p className="text-sm text-foreground/90">{message}</p>
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
