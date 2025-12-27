import { Moon, Sun, Trophy, FileText } from "lucide-react";
import { GamePhase, Role, Winner, getRoleDisplayName, getPhaseDisplayName } from "@/services/api";

interface GameStatusBarProps {
  isNight: boolean;
  turnCount: number;
  playersAlive: number;
  totalPlayers: number;
  phase?: GamePhase;
  role?: Role;
  actionHint?: string;
  isGameOver?: boolean;
  winner?: Winner | null;
  onOpenLogs?: () => void;
}

const GameStatusBar = ({
  isNight,
  turnCount,
  playersAlive,
  totalPlayers,
  phase,
  role,
  actionHint,
  isGameOver,
  winner,
  onOpenLogs,
}: GameStatusBarProps) => {
  return (
    <header className="relative flex items-center justify-between px-6 py-4 bg-card/80 backdrop-blur-sm border-b border-border">
      {/* Decorative glow */}
      <div
        className={`absolute inset-0 opacity-20 transition-colors duration-1000 ${
          isGameOver
            ? winner === "villager"
              ? "bg-gradient-to-r from-transparent via-villager/30 to-transparent"
              : "bg-gradient-to-r from-transparent via-werewolf/30 to-transparent"
            : isNight
            ? "bg-gradient-to-r from-transparent via-moonlight/20 to-transparent"
            : "bg-gradient-to-r from-transparent via-day/20 to-transparent"
        }`}
      />

      {/* Left: Game Title & Role */}
      <div className="relative z-10">
        <h1 className="font-display text-2xl font-bold tracking-wide text-glow-red">
          狼人杀
        </h1>
        {role && (
          <p className="text-xs text-muted-foreground mt-0.5">
            你的身份:{" "}
            <span
              className={
                role === "werewolf" ? "text-werewolf" : "text-villager"
              }
            >
              {getRoleDisplayName(role)}
            </span>
          </p>
        )}
      </div>

      {/* Center: Day/Night Indicator & Phase */}
      <div className="relative z-10 flex flex-col items-center gap-1">
        {isGameOver ? (
          <div className="flex items-center gap-3 px-6 py-2.5 rounded-full border bg-secondary/50 border-accent/30">
            <Trophy className="w-5 h-5 text-accent animate-pulse" />
            <span className="font-display text-lg uppercase tracking-widest text-accent">
              游戏结束
            </span>
            <span
              className={`font-medium ${
                winner === "villager" ? "text-villager" : "text-werewolf"
              }`}
            >
              {winner === "villager" ? "好人胜利" : "狼人胜利"}
            </span>
          </div>
        ) : (
          <>
            <div
              className={`flex items-center gap-3 px-6 py-2.5 rounded-full border transition-all duration-500 ${
                isNight
                  ? "bg-secondary/50 border-moonlight/30 shadow-glow-blue"
                  : "bg-day/10 border-day/30 shadow-[0_0_20px_hsl(45_90%_55%/0.3)]"
              }`}
            >
              {isNight ? (
                <Moon className="w-5 h-5 text-moonlight animate-pulse-glow" />
              ) : (
                <Sun className="w-5 h-5 text-day animate-pulse-glow" />
              )}
              <span
                className={`font-display text-lg uppercase tracking-widest ${
                  isNight ? "text-moonlight text-glow-blue" : "text-day"
                }`}
              >
                {isNight ? "夜晚" : "白天"}
              </span>
              <span className="text-muted-foreground font-medium">
                第 {turnCount} 天
              </span>
            </div>
            {phase && (
              <span className="text-xs text-muted-foreground">
                {getPhaseDisplayName(phase)}
              </span>
            )}
          </>
        )}
      </div>

      {/* Right: Player Count */}
      <div className="relative z-10 flex items-center gap-3">
        {onOpenLogs && (
          <button
            type="button"
            onClick={onOpenLogs}
            className="inline-flex items-center justify-center rounded-full p-2 bg-muted/60 hover:bg-muted transition-colors"
            title="系统日志"
            aria-label="系统日志"
          >
            <FileText className="w-4 h-4 text-foreground" />
          </button>
        )}

        <div className="text-right">
          <p className="text-sm text-muted-foreground">存活玩家</p>
          <p className="font-display text-xl">
            <span className="text-villager">{playersAlive}</span>
            <span className="text-muted-foreground mx-1">/</span>
            <span className="text-foreground">{totalPlayers}</span>
          </p>
        </div>
      </div>
    </header>
  );
};

export default GameStatusBar;
