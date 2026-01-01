import PlayerCard from "./PlayerCard";
import { Users } from "lucide-react";
import { PendingAction, Role } from "@/services/api";
import { useTranslation } from "react-i18next";
import { useIsMobile } from "@/hooks/use-mobile";

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
  nightKillTarget?: number | null; // For witch save phase - highlight the kill target
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
  nightKillTarget,
}: PlayerGridProps) => {
  const { t } = useTranslation('common');
  const isMobile = useIsMobile();

  // Determine which players can be selected based on pending action
  const selectableIds = pendingAction?.choices || [];

  // Circular Layout Calculations
  // We use percentages to ensure responsiveness across different screen sizes.
  // Center of the container is at 50% width, 50% height.
  // Radius is set to 38-42% of the container to leave room for the cards.
  const totalPlayers = players.length;
  const radiusPercent = isMobile ? 38 : 42;

  return (
    <div className={`bg-card/50 rounded-xl border border-border flex flex-col ${isMobile ? 'p-2 h-full' : 'p-3 h-[600px]'}`}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-border shrink-0">
        <Users className="w-4 h-4 text-accent" />
        <h2 className="font-display text-sm font-semibold text-foreground">
          {t('player_grid.title')}
        </h2>
        <span className="ml-auto text-xs text-muted-foreground">
          {pendingAction ? t('player_grid.select_target') : ""}
        </span>
      </div>

      {/* Circular Grid */}
      <div className="relative flex-1 w-full aspect-square mx-auto">
        {players.map((player, index) => {
          // Check if this player is a wolf teammate (for any wolf role)
          const isWolfRole = myRole === "werewolf" || myRole === "wolf_king" || myRole === "white_wolf_king";
          const isWolfTeammate =
            isWolfRole && wolfTeammates.includes(player.seatId);

          // Check verification result (for seer role)
          const verificationResult = verifiedResults[player.seatId];

          // Get teammate's vote target (for werewolf role)
          const wolfVote = wolfVotesVisible[player.seatId];

          // Check if player is selectable
          const isSelectable =
            selectableIds.length === 0 ||
            selectableIds.includes(player.seatId);

          // Calculate circular position
          // Seat ID 1 starts at -90 degrees (12 o'clock)
          // Angle increases clockwise
          // Formula: angle = (index * 360 / total) - 90
          const angleDeg = (index * 360) / totalPlayers - 90;
          const angleRad = (angleDeg * Math.PI) / 180;

          const left = 50 + radiusPercent * Math.cos(angleRad);
          const top = 50 + radiusPercent * Math.sin(angleRad);

          return (
            <div
              key={player.id}
              className="absolute transform -translate-x-1/2 -translate-y-1/2 transition-all duration-500 ease-in-out"
              style={{
                left: `${left}%`,
                top: `${top}%`,
                width: isMobile ? '3.5rem' : '5rem'
              }}
            >
              <PlayerCard
                seatId={player.seatId}
                name={player.name}
                isUser={player.isUser}
                isAlive={player.isAlive}
                isSelected={selectedPlayerId === player.id}
                role={player.role}
                onSelect={onSelectPlayer}
                isCurrentActor={
                  // 只在发言阶段显示边框，真实玩家显示黄色边框
                  pendingAction?.type === "speak" && player.isUser
                }
                isWolfTeammate={isWolfTeammate}
                verificationResult={verificationResult}
                wolfVote={wolfVote}
                isSelectable={isSelectable}
                isKillTarget={
                  // Show kill target highlight for witch save phase
                  myRole === "witch" &&
                  pendingAction?.type === "save" &&
                  nightKillTarget === player.seatId
                }
              />
            </div>
          );
        })}
      </div>

      {/* Legend */}
      {myRole && (
        <div className="mt-4 pt-3 border-t border-border">
          <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
            {(myRole === "werewolf" || myRole === "wolf_king" || myRole === "white_wolf_king") && (
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-werewolf" />
                <span>{t('player_grid.wolf_teammate')}</span>
              </div>
            )}
            {myRole === "seer" && (
              <>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-villager" />
                  <span>{t('player_grid.good')}</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-werewolf" />
                  <span>{t('player_grid.werewolf')}</span>
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
