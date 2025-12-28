import { useTranslation } from "react-i18next";
import { parseVoteResult, formatVoteStats, isVoteResultMessage } from "@/utils/voteUtils";

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
  const { i18n } = useTranslation();

  if (isSystem) {
    // Check if this is a vote result message
    if (isVoteResultMessage(message)) {
      const voteStats = parseVoteResult(message);

      if (voteStats && voteStats.voteCount.size > 0) {
        const formattedVotes = formatVoteStats(voteStats, i18n.language);

        return (
          <div className="flex justify-center my-3 animate-slide-up">
            <div className="flex flex-col items-center gap-2 px-4 py-3 rounded-lg bg-accent/10 border border-accent/20">
              {/* Vote Result Header */}
              <div className="text-accent text-sm font-medium">
                {i18n.language === "zh" ? "投票结果" : "Vote Result"}
              </div>

              {/* Vote Stats - Horizontal Layout */}
              <div className="flex flex-row flex-wrap gap-2 justify-center">
                {formattedVotes.map((vote, index) => (
                  <div
                    key={index}
                    className="px-3 py-1 rounded-full bg-accent/20 border border-accent/30 text-accent text-sm font-semibold"
                  >
                    {vote}
                  </div>
                ))}
              </div>

              {/* Abstain count if any */}
              {voteStats.abstainCount > 0 && (
                <div className="text-xs text-muted-foreground">
                  {i18n.language === "zh"
                    ? `${voteStats.abstainCount}人弃票`
                    : `${voteStats.abstainCount} abstained`}
                </div>
              )}
            </div>
          </div>
        );
      }
    }

    // Regular system message
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
