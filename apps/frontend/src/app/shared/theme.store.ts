import { computed } from '@angular/core';
import {
  patchState,
  signalStore,
  withComputed,
  withMethods,
  withState,
  withHooks,
} from '@ngrx/signals';

interface ThemeState {
  isDarkMode: boolean;
}

const initialState: ThemeState = {
  isDarkMode: false,
};

export const ThemeStore = signalStore(
  { providedIn: 'root' },
  withState(initialState),
  withComputed((store) => ({
    theme: computed(() => (store.isDarkMode() ? 'dark' : 'light')),
  })),
  withMethods((store) => ({
    initializeTheme(): void {
      // Check localStorage first
      const savedTheme = localStorage.getItem('theme');
      if (savedTheme) {
        const isDarkMode = savedTheme === 'dark';
        patchState(store, { isDarkMode });
        this.applyTheme(isDarkMode);
      } else {
        // Check system preference
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        patchState(store, { isDarkMode: prefersDark });
        this.applyTheme(prefersDark);
      }

      // Listen for system theme changes
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        const isDarkMode = e.matches;
        patchState(store, { isDarkMode });
        this.applyTheme(isDarkMode);
      });
    },

    toggleTheme(): void {
      const newDarkMode = !store.isDarkMode();
      patchState(store, { isDarkMode: newDarkMode });
      this.applyTheme(newDarkMode);
      localStorage.setItem('theme', newDarkMode ? 'dark' : 'light');
    },

    setTheme(isDarkMode: boolean): void {
      patchState(store, { isDarkMode });
      this.applyTheme(isDarkMode);
      localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
    },

    applyTheme(isDarkMode: boolean): void {
      if (isDarkMode) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    },
  })),
  withHooks({
    onInit(store) {
      store.initializeTheme();
    },
  })
);