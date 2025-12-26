import { useState, useMemo } from "react";
import GameStatusBar from "@/components/game/GameStatusBar";
import ChatLog from "@/components/game/ChatLog";
import PlayerGrid from "@/components/game/PlayerGrid";
import GameActions from "@/components/game/GameActions";
import GameLobby from "@/components/game/GameLobby";
import DebugLog from "@/components/game/DebugLog";
import { toast } from "sonner";
import { useGame } from "@/hooks/useGame";
import {
  getRoleDisplayName,
  getPhaseDisplayName,
  isNightPhase,
} from "@/services/api";

const Index = () => {
  const {
    gameId,
    gameState,
    isLoading,
    isStarting,
    error,
    isNight,
    needsAction,
    isGameOver,
    startGame,
    speak,
    vote,
    kill,
    verify,
    save,
    poison,
    shoot,
    skip,
    isSubmitting,
  } = useGame({ autoStep: true, stepInterval: 1000 });

  const [selectedPlayerId, setSelectedPlayerId] = useState<number | null>(null);

  // Transform game state to UI format
  const players = useMemo(() => {
    if (!gameState) return [];
    return gameState.players.map((p) => ({
      id: p.seat_id,
      name: p.is_human ? "You" : p.name || `Player ${p.seat_id}`,
      isUser: p.is_human,
      isAlive: p.is_alive,
      // Show role for: 1) Human player always, 2) All players when game is finished
      role: p.role || (p.is_human ? gameState.my_role : undefined),
      seatId: p.seat_id,
    }));
  }, [gameState]);

  // Transform messages to UI format
  const messages = useMemo(() => {
    if (!gameState) return [];
    return gameState.message_log.map((m, idx) => {
      const player = gameState.players.find((p) => p.seat_id === m.seat_id);
      const isSystem = m.type === "system" || m.seat_id === 0;
      const isUser = m.seat_id === gameState.my_seat;
      return {
        id: idx + 1,
        sender: isSystem
          ? "System"
          : isUser
          ? "You"
          : player?.name || `${m.seat_id}号`,
        message: m.text,
        isUser,
        isSystem,
        timestamp: "",
        day: m.day,
      };
    });
  }, [gameState]);

  // Transform debug logs from game actions and phases
  const debugLogs = useMemo(() => {
    if (!gameState) return [];

    const logs: any[] = [];
    let logId = 1;

    // Add phase changes
    logs.push({
      id: logId++,
      timestamp: new Date().toLocaleTimeString("zh-CN", { hour12: false }),
      type: "phase",
      message: `当前阶段: ${getPhaseDisplayName(gameState.phase)} | 第${gameState.day}天`,
    });

    // Add game status
    logs.push({
      id: logId++,
      timestamp: new Date().toLocaleTimeString("zh-CN", { hour12: false }),
      type: "info",
      message: `游戏状态: ${gameState.status} | 存活玩家: ${gameState.players.filter(p => p.is_alive).length}/${gameState.players.length}`,
    });

    // Add pending action info
    if (gameState.pending_action) {
      logs.push({
        id: logId++,
        timestamp: new Date().toLocaleTimeString("zh-CN", { hour12: false }),
        type: "action",
        message: `等待行动: ${gameState.pending_action.message}\n可选目标: [${gameState.pending_action.choices.join(", ")}]`,
      });
    }

    // Add role-specific info
    if (gameState.my_role) {
      logs.push({
        id: logId++,
        timestamp: new Date().toLocaleTimeString("zh-CN", { hour12: false }),
        type: "info",
        message: `你的身份: ${getRoleDisplayName(gameState.my_role)} | 座位号: ${gameState.my_seat}`,
      });
    }

    // Add wolf teammates info
    if (gameState.wolf_teammates && gameState.wolf_teammates.length > 0) {
      logs.push({
        id: logId++,
        timestamp: new Date().toLocaleTimeString("zh-CN", { hour12: false }),
        type: "info",
        message: `狼队友: ${gameState.wolf_teammates.join(", ")}号`,
      });
    }

    // Add seer verification results
    if (gameState.verified_results && Object.keys(gameState.verified_results).length > 0) {
      const verifications = Object.entries(gameState.verified_results)
        .map(([seat, isWolf]) => `${seat}号: ${isWolf ? "狼人" : "好人"}`)
        .join(", ");
      logs.push({
        id: logId++,
        timestamp: new Date().toLocaleTimeString("zh-CN", { hour12: false }),
        type: "info",
        message: `查验结果: ${verifications}`,
      });
    }

    // Add recent messages as debug info
    const recentMessages = gameState.message_log.slice(-5);
    recentMessages.forEach((msg) => {
      logs.push({
        id: logId++,
        timestamp: new Date().toLocaleTimeString("zh-CN", { hour12: false }),
        type: msg.type === "system" ? "phase" : "ai",
        message: `[${msg.seat_id === 0 ? "系统" : `${msg.seat_id}号`}] ${msg.text}`,
      });
    });

    return logs;
  }, [gameState]);

  const playersAlive = players.filter((p) => p.isAlive).length;
  const turnCount = gameState?.day || 1;

  // Handle sending message (speech)
  const handleSendMessage = async (message: string) => {
    if (!gameState || !needsAction) return;

    try {
      await speak(message);
      toast.success("发言成功");
    } catch (err) {
      toast.error("发言失败", {
        description: err instanceof Error ? err.message : "Unknown error",
      });
    }
  };

  // Handle vote
  const handleVote = async () => {
    if (!gameState || !needsAction) return;

    const pendingAction = gameState.pending_action;
    if (!pendingAction) return;

    try {
      if (pendingAction.type === "vote") {
        await vote(selectedPlayerId);
        toast.success(
          selectedPlayerId
            ? `投票给 ${selectedPlayerId}号`
            : "弃票"
        );
      } else if (pendingAction.type === "kill" && selectedPlayerId) {
        await kill(selectedPlayerId);
        toast.success(`选择击杀 ${selectedPlayerId}号`);
      } else if (pendingAction.type === "shoot") {
        await shoot(selectedPlayerId);
        toast.success(
          selectedPlayerId
            ? `开枪带走 ${selectedPlayerId}号`
            : "放弃开枪"
        );
      }
      setSelectedPlayerId(null);
    } catch (err) {
      toast.error("操作失败", {
        description: err instanceof Error ? err.message : "Unknown error",
      });
    }
  };

  // Handle skill use
  const handleUseSkill = async () => {
    if (!gameState || !needsAction) return;

    const pendingAction = gameState.pending_action;
    if (!pendingAction) return;

    try {
      switch (pendingAction.type) {
        case "verify":
          if (selectedPlayerId) {
            await verify(selectedPlayerId);
            toast.info(`查验 ${selectedPlayerId}号`);
          }
          break;
        case "save":
          if (selectedPlayerId === gameState.night_kill_target) {
            await save();
            toast.success("使用解药");
          } else {
            await skip();
            toast.info("跳过");
          }
          break;
        case "poison":
          if (selectedPlayerId && selectedPlayerId !== 0) {
            await poison(selectedPlayerId);
            toast.success(`毒杀 ${selectedPlayerId}号`);
          } else {
            await skip();
            toast.info("跳过");
          }
          break;
        default:
          await skip();
      }
      setSelectedPlayerId(null);
    } catch (err) {
      toast.error("技能使用失败", {
        description: err instanceof Error ? err.message : "Unknown error",
      });
    }
  };

  const handleSelectPlayer = (id: number) => {
    setSelectedPlayerId(selectedPlayerId === id ? null : id);
  };

  // Handle start game
  const handleStartGame = async () => {
    try {
      await startGame(1); // Human at seat 1
      toast.success("游戏开始！");
    } catch (err) {
      toast.error("创建游戏失败", {
        description: err instanceof Error ? err.message : "Unknown error",
      });
    }
  };

  // Show lobby if no game
  if (!gameId) {
    return (
      <GameLobby
        onStartGame={handleStartGame}
        isLoading={isStarting}
        error={error}
      />
    );
  }

  // Determine action button states
  const canVote =
    needsAction &&
    gameState?.pending_action?.type &&
    ["vote", "kill", "shoot"].includes(gameState.pending_action.type);
  const canUseSkill =
    needsAction &&
    gameState?.pending_action?.type &&
    ["verify", "save", "poison"].includes(gameState.pending_action.type);
  const canSpeak =
    needsAction && gameState?.pending_action?.type === "speak";

  // Get action hint
  const actionHint = gameState?.pending_action?.message || "";

  return (
    <div className="flex flex-col h-screen bg-background overflow-hidden">
      {/* Atmospheric background gradient */}
      <div
        className={`fixed inset-0 transition-all duration-1000 pointer-events-none ${
          isNight
            ? "bg-gradient-to-b from-night via-background to-background"
            : "bg-gradient-to-b from-background via-background to-background"
        }`}
      />

      {/* Moon/Sun glow effect */}
      <div
        className={`fixed top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] rounded-full blur-3xl transition-all duration-1000 pointer-events-none ${
          isNight ? "bg-moonlight/5" : "bg-day/5"
        }`}
      />

      {/* Status Bar */}
      <div className="relative z-10">
        <GameStatusBar
          isNight={isNight}
          turnCount={turnCount}
          playersAlive={playersAlive}
          totalPlayers={players.length}
          phase={gameState?.phase}
          role={gameState?.my_role}
          actionHint={actionHint}
          isGameOver={isGameOver}
          winner={gameState?.winner}
        />
      </div>

      {/* Main Content */}
      <div className="relative z-10 flex flex-1 overflow-hidden p-4 gap-4">
        {/* Chat Area */}
        <div className="flex-1 flex flex-col min-w-0">
          <ChatLog messages={messages} isLoading={isLoading} />
        </div>

        {/* Right Sidebar: Players + Debug Log */}
        <div className="w-80 shrink-0 flex flex-col gap-4">
          {/* Players Grid */}
          <div className="flex-shrink-0">
            <PlayerGrid
              players={players}
              selectedPlayerId={selectedPlayerId}
              onSelectPlayer={handleSelectPlayer}
              currentActor={gameState?.current_actor}
              pendingAction={gameState?.pending_action}
              wolfTeammates={gameState?.wolf_teammates}
              verifiedResults={gameState?.verified_results}
              myRole={gameState?.my_role}
            />
          </div>

          {/* Debug Log Panel */}
          <div className="flex-1 min-h-0">
            <DebugLog entries={debugLogs} isLoading={isLoading} />
          </div>
        </div>
      </div>

      {/* Actions Bar */}
      <div className="relative z-10">
        <GameActions
          onSendMessage={handleSendMessage}
          onVote={handleVote}
          onUseSkill={handleUseSkill}
          canVote={canVote && selectedPlayerId !== null}
          canUseSkill={canUseSkill}
          canSpeak={canSpeak}
          isNight={isNight}
          isSubmitting={isSubmitting}
          pendingAction={gameState?.pending_action}
        />
      </div>
    </div>
  );
};

export default Index;
