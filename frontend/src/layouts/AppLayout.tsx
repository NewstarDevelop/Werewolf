/**
 * AppLayout - Application shell with sidebar and main content area
 * Provides responsive layout with collapsible sidebar
 */
import { Outlet } from 'react-router-dom';
import {
  SidebarProvider,
  SidebarInset,
} from '@/components/ui/sidebar';
import { AppSidebar } from '@/components/navigation/AppSidebar';
import { GlobalHeader } from '@/components/layout/GlobalHeader';

/**
 * AppLayout - Main application layout wrapper
 *
 * Features:
 * - Responsive sidebar (drawer on mobile, collapsible on desktop)
 * - Global header with notifications
 * - Persistent state via cookies (handled by SidebarProvider)
 * - Keyboard shortcut (Cmd/Ctrl+B) to toggle (handled by SidebarProvider)
 */
export function AppLayout() {
  return (
    <SidebarProvider defaultOpen={true}>
      <AppSidebar />
      <SidebarInset>
        {/* Global header with sidebar trigger and notifications */}
        <GlobalHeader />
        {/* Main content area */}
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}

export default AppLayout;
