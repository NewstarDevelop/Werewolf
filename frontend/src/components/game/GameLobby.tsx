import { Button } from "@/components/ui/button";
import { Moon, Users, Loader2 } from "lucide-react";

interface GameLobbyProps {
  onStartGame: () => void;
  isLoading: boolean;
  error: string | null;
}

const GameLobby = ({ onStartGame, isLoading, error }: GameLobbyProps) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-background">
      {/* Background effects */}
      <div className="fixed inset-0 bg-gradient-to-b from-night via-background to-background pointer-events-none" />
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] rounded-full blur-3xl bg-moonlight/5 pointer-events-none" />

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center gap-8 p-8">
        {/* Logo/Title */}
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <Moon className="w-24 h-24 text-moonlight animate-pulse" />
            <div className="absolute inset-0 w-24 h-24 bg-moonlight/20 rounded-full blur-xl" />
          </div>
          <h1 className="font-display text-5xl text-foreground tracking-wider">
            狼人杀
          </h1>
          <p className="text-muted-foreground text-lg">
            Werewolf AI Game
          </p>
        </div>

        {/* Game Info */}
        <div className="flex items-center gap-6 text-muted-foreground">
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            <span>9 玩家</span>
          </div>
          <div className="text-sm">
            3狼人 · 3村民 · 预言家 · 女巫 · 猎人
          </div>
        </div>

        {/* Start Button */}
        <Button
          size="lg"
          variant="default"
          onClick={onStartGame}
          disabled={isLoading}
          className="px-12 py-6 text-lg font-display tracking-wider bg-werewolf hover:bg-werewolf/90"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              创建游戏中...
            </>
          ) : (
            "开始游戏"
          )}
        </Button>

        {/* Error message */}
        {error && (
          <div className="text-werewolf text-sm bg-werewolf/10 px-4 py-2 rounded-lg">
            {error}
          </div>
        )}

        {/* Instructions */}
        <div className="max-w-md text-center text-sm text-muted-foreground mt-4">
          <p>
            你将与 8 个 AI 玩家进行对战。
            <br />
            根据你的角色，在白天发言投票，在夜晚使用技能。
            <br />
            找出狼人，或者隐藏身份存活到最后！
          </p>
        </div>
      </div>
    </div>
  );
};

export default GameLobby;
