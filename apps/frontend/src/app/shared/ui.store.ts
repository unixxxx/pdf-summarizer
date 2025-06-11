import { computed } from '@angular/core';
import {
  patchState,
  signalStore,
  withComputed,
  withMethods,
  withState,
} from '@ngrx/signals';

export interface Notification {
  id: string;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
  createdAt: Date;
}

interface UIState {
  globalLoading: boolean;
  globalLoadingMessage: string | null;
  globalError: string | null;
  notifications: Notification[];
  mobileMenuOpen: boolean;
  sidebarCollapsed: boolean;
}

const initialState: UIState = {
  globalLoading: false,
  globalLoadingMessage: null,
  globalError: null,
  notifications: [],
  mobileMenuOpen: false,
  sidebarCollapsed: false,
};

export const UIStore = signalStore(
  { providedIn: 'root' },
  withState(initialState),
  withComputed((store) => ({
    hasNotifications: computed(() => store.notifications().length > 0),
    latestNotification: computed(() => {
      const notifications = store.notifications();
      return notifications.length > 0 ? notifications[0] : null;
    }),
  })),
  withMethods((store) => ({
    // Global Loading
    showGlobalLoading(message?: string): void {
      patchState(store, {
        globalLoading: true,
        globalLoadingMessage: message || null,
      });
    },

    hideGlobalLoading(): void {
      patchState(store, {
        globalLoading: false,
        globalLoadingMessage: null,
      });
    },

    // Global Error
    setGlobalError(error: string): void {
      patchState(store, { globalError: error });
      // Also show as error notification
      this.showNotification(error, 'error');
    },

    clearGlobalError(): void {
      patchState(store, { globalError: null });
    },

    // Notifications
    showNotification(
      message: string,
      type: Notification['type'] = 'info',
      duration = 5000
    ): void {
      const notification: Notification = {
        id: this.generateId(),
        message,
        type,
        duration,
        createdAt: new Date(),
      };

      patchState(store, {
        notifications: [notification, ...store.notifications()],
      });

      // Auto-remove after duration
      if (duration > 0) {
        setTimeout(() => {
          this.removeNotification(notification.id);
        }, duration);
      }
    },

    showSuccess(message: string, duration?: number): void {
      this.showNotification(message, 'success', duration);
    },

    showError(message: string, duration?: number): void {
      this.showNotification(message, 'error', duration);
    },

    showWarning(message: string, duration?: number): void {
      this.showNotification(message, 'warning', duration);
    },

    showInfo(message: string, duration?: number): void {
      this.showNotification(message, 'info', duration);
    },

    removeNotification(id: string): void {
      patchState(store, {
        notifications: store.notifications().filter((n) => n.id !== id),
      });
    },

    clearAllNotifications(): void {
      patchState(store, { notifications: [] });
    },

    // Mobile Menu
    toggleMobileMenu(): void {
      patchState(store, { mobileMenuOpen: !store.mobileMenuOpen() });
    },

    openMobileMenu(): void {
      patchState(store, { mobileMenuOpen: true });
    },

    closeMobileMenu(): void {
      patchState(store, { mobileMenuOpen: false });
    },

    // Sidebar
    toggleSidebar(): void {
      patchState(store, { sidebarCollapsed: !store.sidebarCollapsed() });
    },

    setSidebarCollapsed(collapsed: boolean): void {
      patchState(store, { sidebarCollapsed: collapsed });
    },

    // Utility methods
    async withGlobalLoading<T>(
      operation: () => Promise<T>,
      loadingMessage?: string
    ): Promise<T> {
      this.showGlobalLoading(loadingMessage);
      try {
        const result = await operation();
        this.hideGlobalLoading();
        return result;
      } catch (error) {
        this.hideGlobalLoading();
        if (error instanceof Error) {
          this.setGlobalError(error.message);
        }
        throw error;
      }
    },

    // Private helpers
    generateId(): string {
      return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    },
  }))
);