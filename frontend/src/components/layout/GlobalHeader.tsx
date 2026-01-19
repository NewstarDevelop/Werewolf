/**
 * GlobalHeader - Unified top header for desktop/mobile
 *
 * Features:
 * - Sidebar trigger (mobile)
 * - Notification center
 * - User navigation (future)
 */
import { SidebarTrigger } from '@/components/ui/sidebar';
import { Separator } from '@/components/ui/separator';
import { NotificationCenter } from '@/components/notifications';
import { useAuth } from '@/contexts/AuthContext';

export function GlobalHeader() {
  const { user } = useAuth();

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-sidebar-border px-4">
      {/* Left side: Sidebar trigger (mobile only via CSS) */}
      <div className="flex items-center gap-2 md:hidden">
        <SidebarTrigger className="-ml-1" aria-label="Toggle Sidebar" />
        <Separator orientation="vertical" className="mr-2 h-4" />
        <span className="font-semibold text-sidebar-foreground">Werewolf</span>
      </div>

      {/* Spacer for desktop */}
      <div className="hidden md:block" />

      {/* Right side: Notifications + User menu */}
      <div className="flex items-center gap-2">
        {/* Only show notifications for logged-in users */}
        {user && <NotificationCenter />}
      </div>
    </header>
  );
}

export default GlobalHeader;
