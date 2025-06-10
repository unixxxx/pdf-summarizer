import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthStore } from '../auth.store';
import { ThemeStore } from '../../shared/theme.store';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div
      class="min-h-screen bg-background gradient-mesh flex flex-col justify-center py-12 sm:px-6 lg:px-8 transition-theme"
    >
      <div class="sm:mx-auto sm:w-full sm:max-w-md animate-fade-in">
        <div class="text-center">
          <div
            class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-accent-500 shadow-lg mb-4 animate-scale-in"
          >
            <svg
              class="w-8 h-8 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <h2
            class="text-4xl font-bold bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent"
          >
            PDF Summarizer
          </h2>
          <p class="mt-3 text-lg text-muted-foreground">
            Transform your PDFs into concise, intelligent summaries with AI
          </p>
        </div>
      </div>

      <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md animate-slide-up">
        <div class="glass rounded-2xl shadow-xl p-8 space-y-6">
          <div class="text-center">
            <h3 class="text-lg font-semibold text-foreground">Welcome back</h3>
            <p class="mt-1 text-sm text-muted-foreground">
              Sign in to your account to continue
            </p>
          </div>

          <div class="space-y-3">
            <button
              (click)="login('google')"
              [disabled]="isLoading()"
              class="w-full flex justify-center items-center px-5 py-3 border border-border rounded-xl text-sm font-medium text-foreground bg-card hover:bg-muted transition-theme group relative overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div
                class="absolute inset-0 bg-gradient-to-r from-primary-500/10 to-accent-500/10 opacity-0 group-hover:opacity-100 transition-opacity"
              ></div>
              <svg class="w-5 h-5 mr-3 relative z-10" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              <span class="relative z-10">Continue with Google</span>
            </button>

            <button
              (click)="login('github')"
              [disabled]="isLoading()"
              class="w-full flex justify-center items-center px-5 py-3 rounded-xl text-sm font-medium text-white bg-gradient-to-r from-gray-800 to-gray-900 hover:from-gray-700 hover:to-gray-800 transition-all transform hover:scale-[1.02] shadow-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              <svg class="w-5 h-5 mr-3" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fill-rule="evenodd"
                  d="M10 0C4.477 0 0 4.484 0 10.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0110 4.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.203 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0020 10.017C20 4.484 15.522 0 10 0z"
                  clip-rule="evenodd"
                />
              </svg>
              Continue with GitHub
            </button>
          </div>

          <div class="relative">
            <div class="absolute inset-0 flex items-center">
              <div class="w-full border-t border-border"></div>
            </div>
            <div class="relative flex justify-center text-xs">
              <span class="px-4 bg-card text-muted-foreground"
                >Secure authentication</span
              >
            </div>
          </div>

          <div
            class="flex items-center justify-center space-x-1 text-xs text-muted-foreground"
          >
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
            <span>Your data is encrypted and secure</span>
          </div>
        </div>
      </div>

      <!-- Theme toggle for login page -->
      <div class="fixed bottom-4 right-4">
        <button
          (click)="toggleTheme()"
          class="p-3 rounded-xl bg-card border border-border shadow-lg hover:shadow-xl transition-all hover:scale-110"
          [attr.aria-label]="
            isDarkMode() ? 'Switch to light mode' : 'Switch to dark mode'
          "
        >
          <svg
            *ngIf="!isDarkMode()"
            class="w-5 h-5 text-muted-foreground"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
            />
          </svg>
          <svg
            *ngIf="isDarkMode()"
            class="w-5 h-5 text-muted-foreground"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
            />
          </svg>
        </button>
      </div>
    </div>
  `,
})
export class LoginComponent {
  private readonly authStore = inject(AuthStore);
  private readonly themeStore = inject(ThemeStore);

  // Expose store selectors for template
  readonly isLoading = this.authStore.isLoading;
  readonly isDarkMode = this.themeStore.isDarkMode;

  login(provider: 'google' | 'github') {
    this.authStore.login(provider);
  }

  toggleTheme() {
    this.themeStore.toggleTheme();
  }
}
