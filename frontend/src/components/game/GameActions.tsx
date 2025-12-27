import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Send, Vote, Sparkles, Loader2, SkipForward } from "lucide-react";
import { PendingAction } from "@/services/api";
import { useTranslation } from "react-i18next";

interface GameActionsProps {
  onSendMessage: (message: string) => void;
  onVote: () => void;
  onUseSkill: () => void;
  canVote: boolean;
  canUseSkill: boolean;
  canSpeak?: boolean;
  isNight: boolean;
  isSubmitting?: boolean;
  pendingAction?: PendingAction | null;
}

const GameActions = ({
  onSendMessage,
  onVote,
  onUseSkill,
  canVote,
  canUseSkill,
  canSpeak,
  isNight,
  isSubmitting,
  pendingAction,
}: GameActionsProps) => {
  const [message, setMessage] = useState("");
  const { t } = useTranslation('game');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && canSpeak) {
      onSendMessage(message.trim());
      setMessage("");
    }
  };

  // Get action button label based on pending action type
  const getVoteButtonLabel = () => {
    if (!pendingAction) return t('action.vote');
    return t(`action.${pendingAction.type}`);
  };

  const getSkillButtonLabel = () => {
    if (!pendingAction) return t('action.confirm');
    return t(`action.${pendingAction.type}`);
  };

  // Determine if we should show skip button
  const showSkipButton =
    pendingAction &&
    ["save", "poison", "shoot", "vote"].includes(pendingAction.type) &&
    pendingAction.choices.includes(0);

  return (
    <div className="bg-card/80 backdrop-blur-sm border-t border-border p-4">
      <div className="flex flex-col gap-3">
        {/* Action hint */}
        {pendingAction?.message && (
          <div className="text-center text-sm text-accent bg-accent/10 py-2 px-4 rounded-lg">
            {pendingAction.message}
          </div>
        )}

        {/* Chat Input */}
        <form onSubmit={handleSubmit} className="flex gap-2">
          <div className="flex-1 relative">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder={
                canSpeak
                  ? t('message.enter_message')
                  : isNight
                  ? t('status.night')
                  : t('message.waiting')
              }
              disabled={!canSpeak || isSubmitting}
              className="w-full px-4 py-3 rounded-xl bg-input border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            />
          </div>
          <Button
            type="submit"
            size="icon"
            variant="muted"
            disabled={!canSpeak || !message.trim() || isSubmitting}
            className="h-12 w-12"
          >
            {isSubmitting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </form>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <Button
            variant="vote"
            size="lg"
            onClick={onVote}
            disabled={!canVote || isSubmitting}
            className="flex-1"
          >
            {isSubmitting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Vote className="w-4 h-4" />
            )}
            {getVoteButtonLabel()}
          </Button>

          <Button
            variant="skill"
            size="lg"
            onClick={onUseSkill}
            disabled={!canUseSkill || isSubmitting}
            className="flex-1"
          >
            {isSubmitting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            {getSkillButtonLabel()}
          </Button>

          {showSkipButton && (
            <Button
              variant="muted"
              size="lg"
              onClick={onUseSkill}
              disabled={isSubmitting}
              className="w-24"
            >
              <SkipForward className="w-4 h-4" />
              {t('action.skip')}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default GameActions;
