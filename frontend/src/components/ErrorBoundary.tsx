import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';
import { captureError } from '@/lib/sentry';
import { withTranslation, WithTranslation } from 'react-i18next';

interface Props extends WithTranslation {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundaryClass extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
    captureError(error, { componentStack: errorInfo.componentStack });
  }

  public render() {
    const { t } = this.props;

    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-screen bg-background p-4">
          <Alert variant="destructive" className="max-w-md">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>{t('error.something_went_wrong')}</AlertTitle>
            <AlertDescription className="mt-2">
              <p className="mb-4 text-sm">{this.state.error?.message || t('error.unexpected_error')}</p>
              <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
                {t('error.reload_page')}
              </Button>
            </AlertDescription>
          </Alert>
        </div>
      );
    }

    return this.props.children;
  }
}

// 使用 withTranslation HOC 包装，使组件响应语言切换
export const ErrorBoundary = withTranslation('common')(ErrorBoundaryClass);
