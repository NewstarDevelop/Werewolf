import { Moon, Sun, Trophy, FileText, Brain, TrendingUp } from "lucide-react";
import { GamePhase, Role, Winner, getRoleDisplayName, getPhaseDisplayName } from "@/services/api";
import { useTranslation } from "react-i18next";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

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
  onOpenDebug?: () => void;
  onOpenAnalysis?: () => void;
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
  onOpenDebug,
  onOpenAnalysis,
}: GameStatusBarProps) => {
  const { t } = useTranslation(['common', 'game', 'roles']);

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
          {t('common:app.title')}
        </h1>
        {role && (
          <p className="text-xs text-muted-foreground mt-0.5">
            {t('roles:your_role', { role: getRoleDisplayName(role) })}
          </p>
        )}
      </div>

      {/* Center: Day/Night Indicator & Phase */}
      <div className="relative z-10 flex flex-col items-center gap-1">
        {isGameOver ? (
          <div className="flex items-center gap-3 px-6 py-2.5 rounded-full border bg-secondary/50 border-accent/30">
            <Trophy className="w-5 h-5 text-accent animate-pulse" />
            <span className="font-display text-lg uppercase tracking-widest text-accent">
              {t('game:game_over.title')}
            </span>
            <span
              className={`font-medium ${
                winner === "villager" ? "text-villager" : "text-werewolf"
              }`}
            >
              {winner === "villager" ? t('game:winner.villager') : t('game:winner.werewolf')}
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
                {isNight ? t('game:status.night') : t('game:status.day')}
              </span>
              <span className="text-muted-foreground font-medium">
                {t('game:status.day_count', { count: turnCount })}
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

      {/* Right: Player Count & Controls */}
      <div className="relative z-10 flex items-center gap-3">
        <LanguageSwitcher />

        {isGameOver && onOpenAnalysis && (
          <button
            type="button"
            onClick={onOpenAnalysis}
            className="inline-flex items-center gap-2 rounded-full px-4 py-2 bg-accent/20 hover:bg-accent/30 transition-colors border border-accent/30"
            title={t('common:ui.game_analysis')}
            aria-label={t('common:ui.game_analysis')}
          >
            <TrendingUp className="w-4 h-4 text-accent" />
            <span className="text-sm font-medium text-accent">{t('common:ui.game_analysis')}</span>
          </button>
        )}

        {onOpenLogs && (
          <button
            type="button"
            onClick={onOpenLogs}
            className="inline-flex items-center justify-center rounded-full p-2 bg-muted/60 hover:bg-muted transition-colors"
            title={t('common:ui.system_log')}
            aria-label={t('common:ui.system_log')}
          >
            <FileText className="w-4 h-4 text-foreground" />
          </button>
        )}

        {onOpenDebug && (
          <button
            type="button"
            onClick={onOpenDebug}
            className="inline-flex items-center justify-center rounded-full p-2 bg-muted/60 hover:bg-muted transition-colors"
            title={t('common:ui.ai_debug')}
            aria-label={t('common:ui.ai_debug')}
          >
            <Brain className="w-4 h-4 text-purple-400" />
          </button>
        )}

        <div className="text-right">
          <p className="text-sm text-muted-foreground">{t('game:status.players_alive')}</p>
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
