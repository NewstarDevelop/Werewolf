import { User, Skull, Shield, Search, Crosshair, FlaskConical, Target } from "lucide-react";
import { getRoleDisplayName, type Role } from "@/services/api";

interface PlayerCardProps {
  seatId: number;
  name: string;
  isUser: boolean;
  isAlive: boolean;
  isSelected: boolean;
  role?: Role;
  avatar?: string;
  onSelect: () => void;
  isCurrentActor?: boolean;
  isWolfTeammate?: boolean;
  verificationResult?: boolean; // true = werewolf, false = good
  isSelectable?: boolean;
}

const PlayerCard = ({
  seatId,
  name,
  isUser,
  isAlive,
  isSelected,
  role,
  onSelect,
  isCurrentActor,
  isWolfTeammate,
  verificationResult,
  isSelectable = true,
}: PlayerCardProps) => {
  const getRoleIcon = () => {
    if (!role) return null;
    switch (role) {
      case "werewolf":
        return <Skull className="w-3 h-3 text-werewolf" />;
      case "seer":
        return <Search className="w-3 h-3 text-moonlight" />;
      case "witch":
        return <FlaskConical className="w-3 h-3 text-purple-400" />;
      case "hunter":
        return <Crosshair className="w-3 h-3 text-orange-400" />;
      case "villager":
        return <User className="w-3 h-3 text-villager" />;
      default:
        return null;
    }
  };

  // Determine background class based on special status
  const getBackgroundClass = () => {
    if (isSelected) return "bg-werewolf/20 scale-105";
    if (isCurrentActor && isUser) return "bg-yellow-400/20 scale-105";
    return "bg-card/50";
  };

  // Determine border color based on special status
  const getBorderClass = () => {
    // Speaking/acting has absolute highest priority - must be checked first!
    if (isCurrentActor && isUser) return "border-2 border-yellow-400 shadow-[0_0_15px_rgba(250,204,21,0.5)] animate-pulse z-50";
    if (isCurrentActor) return "border-2 border-accent animate-pulse z-50";

    // Selection state (second priority)
    if (isSelected) return "border-2 border-werewolf shadow-glow-red";

    // Team/verification states (lower priority, only show when NOT speaking)
    if (isWolfTeammate) return "border-2 border-werewolf/50";
    if (verificationResult === true) return "border-2 border-werewolf/70";
    if (verificationResult === false) return "border-2 border-villager/70";

    // Default state
    return "border border-border hover:border-accent/50";
  };

  return (
    <button
      onClick={onSelect}
      disabled={!isAlive || !isSelectable}
      className={`
        relative group flex flex-col items-center gap-2 p-3 rounded-xl
        transition-all duration-300
        ${
          isAlive && isSelectable
            ? "hover:scale-105 hover:bg-muted/50 cursor-pointer"
            : "opacity-40 cursor-not-allowed"
        }
        ${!isAlive ? "grayscale" : ""}
        ${getBackgroundClass()}
        ${getBorderClass()}
        ${isUser ? "ring-2 ring-accent/30" : ""}
      `}
    >
      {/* Seat number badge */}
      <div className="absolute -top-1 -left-1 w-5 h-5 rounded-full bg-muted border border-border flex items-center justify-center">
        <span className="text-[10px] font-bold text-muted-foreground">
          {seatId}
        </span>
      </div>

      {/* Current actor indicator */}
      {isCurrentActor && isAlive && (
        <div className="absolute -top-1 -right-1">
          <Target className="w-4 h-4 text-accent animate-pulse" />
        </div>
      )}

      {/* Wolf teammate indicator */}
      {isWolfTeammate && !isUser && (
        <div className="absolute -top-1 -right-1">
          <Skull className="w-4 h-4 text-werewolf" />
        </div>
      )}

      {/* Verification result indicator */}
      {verificationResult !== undefined && !isUser && (
        <div
          className={`absolute -top-1 -right-1 w-4 h-4 rounded-full ${
            verificationResult ? "bg-werewolf" : "bg-villager"
          }`}
        />
      )}

      {/* Avatar */}
      <div
        className={`
          relative w-14 h-14 rounded-full flex items-center justify-center
          transition-all duration-300
          ${
            isAlive
              ? isSelected
                ? "bg-werewolf/30 shadow-glow-red"
                : "bg-muted group-hover:bg-accent/20"
              : "bg-muted/50"
          }
        `}
      >
        {isAlive ? (
          <User
            className={`w-7 h-7 ${
              isSelected
                ? "text-werewolf"
                : "text-muted-foreground group-hover:text-accent"
            }`}
          />
        ) : (
          <Skull className="w-7 h-7 text-muted-foreground/50" />
        )}

        {/* Role badge for user */}
        {role && (
          <div className="absolute -bottom-1 -right-1 p-1.5 rounded-full bg-card border border-border">
            {getRoleIcon()}
          </div>
        )}
      </div>

      {/* Name */}
      <div className="text-center min-h-[32px] flex flex-col items-center justify-center">
        <p
          className={`text-xs font-medium truncate max-w-[70px] ${
            isAlive
              ? isSelected
                ? "text-werewolf"
                : "text-foreground"
              : "text-muted-foreground line-through"
          }`}
        >
          {name}
        </p>
        {role && (
          <span className="text-[10px] text-accent uppercase tracking-wider">
            {getRoleDisplayName(role)}
          </span>
        )}
      </div>

      {/* Death overlay */}
      {!isAlive && (
        <div className="absolute inset-0 flex items-center justify-center rounded-xl bg-background/30 backdrop-blur-[1px]">
          <span className="text-xs text-werewolf font-display uppercase tracking-wider">
            出局
          </span>
        </div>
      )}
    </button>
  );
};

export default PlayerCard;
