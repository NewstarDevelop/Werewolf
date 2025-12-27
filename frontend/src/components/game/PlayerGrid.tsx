import PlayerCard from "./PlayerCard";
import { Users } from "lucide-react";
import { PendingAction, Role } from "@/services/api";

interface Player {
  id: number;
  name: string;
  isUser: boolean;
  isAlive: boolean;
  role?: Role;
  seatId: number;
}

interface PlayerGridProps {
  players: Player[];
  selectedPlayerId: number | null;
  onSelectPlayer: (id: number) => void;
  currentActor?: number | null;
  pendingAction?: PendingAction | null;
  wolfTeammates?: number[];
  verifiedResults?: Record<number, boolean>;
  wolfVotesVisible?: Record<number, number>; // teammate_seat -> target_seat
  myRole?: Role;
}

const PlayerGrid = ({
  players,
  selectedPlayerId,
  onSelectPlayer,
  currentActor,
  pendingAction,
  wolfTeammates = [],
  verifiedResults = {},
  wolfVotesVisible = {},
  myRole,
}: PlayerGridProps) => {
  // Determine which players can be selected based on pending action
  const selectableIds = pendingAction?.choices || [];

  return (
    <div className="bg-card/50 rounded-xl border border-border p-4">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-border">
        <Users className="w-4 h-4 text-accent" />
        <h2 className="font-display text-sm uppercase tracking-wider text-foreground">
          玩家
        </h2>
        <span className="ml-auto text-xs text-muted-foreground">
          {pendingAction ? "选择目标" : ""}
        </span>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-3 gap-3">
        {players.map((player) => {
          // Check if this player is a wolf teammate (for werewolf role)
          const isWolfTeammate =
            myRole === "werewolf" && wolfTeammates.includes(player.seatId);

          // Check verification result (for seer role)
          const verificationResult = verifiedResults[player.seatId];

          // Get teammate's vote target (for werewolf role)
          const wolfVote = wolfVotesVisible[player.seatId];

          // Check if player is selectable
          const isSelectable =
            selectableIds.length === 0 ||
            selectableIds.includes(player.seatId);

          return (
            <PlayerCard
              key={player.id}
              seatId={player.seatId}
              name={player.name}
              isUser={player.isUser}
              isAlive={player.isAlive}
              isSelected={selectedPlayerId === player.id}
              role={player.role}
              onSelect={() => isSelectable && onSelectPlayer(player.id)}
              isCurrentActor={
                pendingAction?.type === "speak"
                  ? player.isUser  // 发言阶段：只有真实玩家显示边框
                  : currentActor === player.seatId  // 其他阶段：使用 currentActor
              }
              isWolfTeammate={isWolfTeammate}
              verificationResult={verificationResult}
              wolfVote={wolfVote}
              isSelectable={isSelectable}
            />
          );
        })}
      </div>

      {/* Legend */}
      {myRole && (
        <div className="mt-4 pt-3 border-t border-border">
          <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
            {myRole === "werewolf" && (
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-werewolf" />
                <span>狼队友</span>
              </div>
            )}
            {myRole === "seer" && (
              <>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-villager" />
                  <span>好人</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-werewolf" />
                  <span>狼人</span>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default PlayerGrid;
