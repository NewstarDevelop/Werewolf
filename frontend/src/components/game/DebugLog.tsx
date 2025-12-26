import { useRef, useEffect, useState } from "react";
import { Bug, Maximize2, Minimize2 } from "lucide-react";

interface DebugLogEntry {
  id: number;
  timestamp: string;
  type: "info" | "action" | "phase" | "ai";
  message: string;
}

interface DebugLogProps {
  entries: DebugLogEntry[];
  isLoading?: boolean;
}

const DebugLog = ({ entries, isLoading }: DebugLogProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isMaximized, setIsMaximized] = useState(false);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [entries]);

  const getTypeColor = (type: string) => {
    switch (type) {
      case "info":
        return "text-blue-400";
      case "action":
        return "text-green-400";
      case "phase":
        return "text-purple-400";
      case "ai":
        return "text-orange-400";
      default:
        return "text-muted-foreground";
    }
  };

  const getTypeBadge = (type: string) => {
    switch (type) {
      case "info":
        return "INFO";
      case "action":
        return "ACTION";
      case "phase":
        return "PHASE";
      case "ai":
        return "AI";
      default:
        return type.toUpperCase();
    }
  };

  return (
    <div
      className={`flex flex-col bg-card/50 rounded-xl border border-border overflow-hidden transition-all duration-300 ${
        isMaximized
          ? "fixed inset-4 z-50 shadow-2xl"
          : "h-full"
      }`}
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border bg-muted/30">
        <Bug className="w-4 h-4 text-orange-400" />
        <h2 className="font-display text-sm uppercase tracking-wider text-foreground">
          调试日志
        </h2>
        <span className="ml-auto text-xs text-muted-foreground">
          {entries.length} 条记录
        </span>
        <button
          onClick={() => setIsMaximized(!isMaximized)}
          className="p-1 rounded hover:bg-muted/50 transition-colors"
          title={isMaximized ? "最小化" : "最大化"}
        >
          {isMaximized ? (
            <Minimize2 className="w-4 h-4 text-muted-foreground hover:text-foreground" />
          ) : (
            <Maximize2 className="w-4 h-4 text-muted-foreground hover:text-foreground" />
          )}
        </button>
      </div>

      {/* Log entries */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 scrollbar-thin font-mono text-xs"
      >
        {entries.length === 0 ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            暂无调试信息...
          </div>
        ) : (
          entries.map((entry) => (
            <div
              key={entry.id}
              className="mb-2 pb-2 border-b border-border/30 last:border-0 hover:bg-muted/30 px-2 py-1 rounded transition-colors"
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-muted-foreground/60 text-[10px]">
                  {entry.timestamp}
                </span>
                <span
                  className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${getTypeColor(
                    entry.type
                  )} bg-background/50`}
                >
                  {getTypeBadge(entry.type)}
                </span>
              </div>
              <p className="text-foreground/80 leading-relaxed whitespace-pre-wrap">
                {entry.message}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default DebugLog;
