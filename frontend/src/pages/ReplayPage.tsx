import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Clock, Users, Trophy, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import ChatLog from '@/components/game/ChatLog';
import { useGameReplay } from '@/hooks/useGameReplay';
import { useGameHistoryDetail } from '@/hooks/useGameHistory';
import type { MessageInGame } from '@/services/api';

// 将 MessageInGame 转换为 ChatLog 需要的格式
function convertMessages(messages: MessageInGame[]) {
  return messages.map((msg, index) => ({
    id: index,
    sender: msg.seat_id === 0 ? 'System' : `Player ${msg.seat_id}`,
    message: msg.text,
    isUser: false,
    isSystem: msg.seat_id === 0 || msg.type === 'system',
    timestamp: new Date().toISOString(), // 回放模式不需要实时时间戳
    day: msg.day,
  }));
}

export default function ReplayPage() {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation('common');

  const { data: replayData, isLoading: isLoadingReplay, error: replayError } = useGameReplay(gameId);
  const { data: gameDetail, isLoading: isLoadingDetail } = useGameHistoryDetail(gameId || '');

  const isLoading = isLoadingReplay || isLoadingDetail;

  const handleBack = () => {
    navigate('/history');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4" />
          <p className="text-muted-foreground">{t('ui.loading')}</p>
        </div>
      </div>
    );
  }

  if (replayError || !replayData) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-4xl mx-auto">
          <Button
            variant="ghost"
            onClick={handleBack}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            {t('ui.back')}
          </Button>

          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {t('history.replay_not_available')}
            </AlertDescription>
          </Alert>
        </div>
      </div>
    );
  }

  const messages = convertMessages(replayData.messages);

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-6 max-w-7xl">
        {/* Header */}
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={handleBack}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            {t('ui.back')}
          </Button>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">
                {t('history.game_replay')}
              </h1>
              {gameDetail && (
                <p className="text-muted-foreground">
                  {gameDetail.room_name}
                </p>
              )}
            </div>

            {gameDetail && (
              <div className="flex gap-4">
                <div className="flex items-center gap-2 text-sm">
                  <Users className="w-4 h-4" />
                  <span>{gameDetail.player_count} {t('history.players')}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Trophy className="w-4 h-4" />
                  <span>{t(`game:winner.${gameDetail.winner}`)}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Clock className="w-4 h-4" />
                  <span>{Math.floor(gameDetail.duration_seconds / 60)} {t('ui.minutes')}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Replay Content */}
        <Card className="p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold">{t('history.message_timeline')}</h2>
            <span className="text-sm text-muted-foreground">
              {replayData.total} {t('history.messages')}
            </span>
          </div>

          <div className="h-[600px] border rounded-lg bg-card">
            <ChatLog messages={messages} isLoading={false} />
          </div>

          {gameDetail && (
            <div className="mt-6 p-4 bg-muted rounded-lg">
              <h3 className="font-semibold mb-2">{t('history.your_role')}</h3>
              <p className="text-sm">
                {t(`game:role.${gameDetail.my_role}`)} - {gameDetail.is_winner ? t('history.victory') : t('history.defeat')}
              </p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
