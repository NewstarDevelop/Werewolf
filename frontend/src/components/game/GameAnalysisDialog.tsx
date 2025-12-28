import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Loader2, TrendingUp, Trophy, AlertCircle, AlertTriangle } from "lucide-react";
import { useTranslation } from "react-i18next";
import ReactMarkdown from 'react-markdown';

interface GameAnalysisDialogProps {
  gameId: string;
  isOpen: boolean;
  onClose: () => void;
}

interface AnalysisData {
  game_id: string;
  winner: string;
  total_days: number;
  analysis: string;
  game_summary: {
    total_players: number;
    alive_players: number;
    total_days: number;
    total_speeches: number;
    total_votes: number;
    winner: string;
  };
}

const GameAnalysisDialog = ({ gameId, isOpen, onClose }: GameAnalysisDialogProps) => {
  const { t } = useTranslation(['common', 'game']);
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch analysis when dialog opens
  const fetchAnalysis = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/game/${gameId}/analyze`);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch analysis');
      }

      const data: AnalysisData = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  // Trigger fetch when dialog opens
  const handleOpenChange = (open: boolean) => {
    if (open && !analysis && !isLoading) {
      fetchAnalysis();
    }
    if (!open) {
      onClose();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-4xl h-[90vh] p-0 bg-card border-border">
        <DialogHeader className="px-6 py-4 border-b border-border bg-muted/30">
          <DialogTitle className="flex items-center gap-2 text-xl font-display">
            <TrendingUp className="w-5 h-5 text-accent" />
            {t('common:ui.game_analysis')}
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-hidden">
          {isLoading && (
            <div className="flex flex-col items-center justify-center h-full gap-4">
              <Loader2 className="w-12 h-12 animate-spin text-accent" />
              <p className="text-muted-foreground text-lg">
                {t('game:analysis.generating')}
              </p>
              <p className="text-xs text-muted-foreground">
                {t('game:analysis.may_take_time')}
              </p>
            </div>
          )}

          {error && (
            <div className="flex flex-col items-center justify-center h-full gap-4 px-6">
              <AlertCircle className="w-12 h-12 text-destructive" />
              <p className="text-destructive font-medium">{t('common:ui.analysis_failed')}</p>
              <p className="text-sm text-muted-foreground">{error}</p>
              <Button onClick={fetchAnalysis} variant="outline">
                {t('common:ui.retry')}
              </Button>
            </div>
          )}

          {analysis && !isLoading && (
            <ScrollArea className="h-full px-6 py-4">
              {/* Fallback Mode Warning */}
              {(() => {
                const isFallbackMode = analysis.analysis.includes("备用模式") ||
                                       analysis.analysis.includes("Fallback Mode") ||
                                       analysis.analysis.includes("暂时不可用");

                return isFallbackMode && (
                  <Alert variant="warning" className="mb-4 border-yellow-500/50 bg-yellow-500/10">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertTitle>{t('game:analysis.fallback_mode')}</AlertTitle>
                    <AlertDescription>
                      <p className="mb-2">{t('game:analysis.fallback_hint')}</p>
                      <code className="text-xs bg-muted p-2 rounded block mt-2">
                        ANALYSIS_PROVIDER=openai<br />
                        ANALYSIS_MODEL=gpt-4o
                      </code>
                    </AlertDescription>
                  </Alert>
                );
              })()}

              {/* Game Summary Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <SummaryCard
                  icon={<Trophy className="w-4 h-4" />}
                  label={t('game:game_over.winner_announce', { winner: analysis.winner })}
                  value=""
                  highlight
                />
                <SummaryCard
                  label={t('common:ui.total_days')}
                  value={analysis.total_days.toString()}
                />
                <SummaryCard
                  label={t('common:ui.total_speeches')}
                  value={analysis.game_summary.total_speeches.toString()}
                />
                <SummaryCard
                  label={t('common:ui.total_votes')}
                  value={analysis.game_summary.total_votes.toString()}
                />
              </div>

              {/* AI Analysis Content */}
              <div className="prose prose-invert max-w-none">
                <div className="bg-background/50 rounded-lg p-6 border border-border">
                  <ReactMarkdown
                    className="markdown-content"
                    components={{
                      h1: ({ ...props }) => (
                        <h1 className="text-2xl font-bold mb-4 text-foreground" {...props} />
                      ),
                      h2: ({ ...props }) => (
                        <h2 className="text-xl font-semibold mt-6 mb-3 text-foreground" {...props} />
                      ),
                      h3: ({ ...props }) => (
                        <h3 className="text-lg font-medium mt-4 mb-2 text-foreground" {...props} />
                      ),
                      p: ({ ...props }) => (
                        <p className="mb-3 text-muted-foreground leading-relaxed" {...props} />
                      ),
                      ul: ({ ...props }) => (
                        <ul className="list-disc list-inside mb-3 space-y-1" {...props} />
                      ),
                      ol: ({ ...props }) => (
                        <ol className="list-decimal list-inside mb-3 space-y-1" {...props} />
                      ),
                      li: ({ ...props }) => (
                        <li className="text-muted-foreground" {...props} />
                      ),
                      strong: ({ ...props }) => (
                        <strong className="font-semibold text-foreground" {...props} />
                      ),
                      code: ({ ...props }) => (
                        <code className="bg-muted px-1.5 py-0.5 rounded text-sm" {...props} />
                      ),
                      blockquote: ({ ...props }) => (
                        <blockquote className="border-l-4 border-accent pl-4 italic text-muted-foreground" {...props} />
                      ),
                    }}
                  >
                    {analysis.analysis}
                  </ReactMarkdown>
                </div>
              </div>
            </ScrollArea>
          )}
        </div>

        <div className="px-6 py-4 border-t border-border bg-muted/30">
          <Button
            onClick={() => onClose()}
            className="w-full"
            variant="outline"
          >
            {t('common:ui.close')}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

interface SummaryCardProps {
  icon?: React.ReactNode;
  label: string;
  value: string;
  highlight?: boolean;
}

const SummaryCard = ({ icon, label, value, highlight }: SummaryCardProps) => {
  return (
    <div
      className={`flex flex-col gap-2 p-4 rounded-lg border ${
        highlight
          ? 'bg-accent/10 border-accent/30'
          : 'bg-muted/30 border-border'
      }`}
    >
      {icon && <div className="text-accent">{icon}</div>}
      <p className="text-xs text-muted-foreground">{label}</p>
      {value && (
        <p className="text-lg font-bold text-foreground">{value}</p>
      )}
    </div>
  );
};

export default GameAnalysisDialog;
