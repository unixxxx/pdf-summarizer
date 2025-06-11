import { Component, inject, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, RouterOutlet } from '@angular/router';
import { trigger, style, transition, animate, query } from '@angular/animations';
import { AuthStore } from '../auth/auth.store';
import { ThemeStore } from '../shared/theme.store';
import { UIStore } from '../shared/ui.store';
import { NotificationsComponent } from '../shared/notifications.component';
import { GlobalLoadingComponent } from '../shared/global-loading.component';

const routeAnimations = trigger('routeAnimations', [
  transition('* <=> *', [
    query(':enter, :leave', [
      style({
        position: 'absolute',
        left: 0,
        width: '100%',
        opacity: 0,
        transform: 'scale(0.95) translateY(20px)',
      }),
    ], { optional: true }),
    query(':enter', [
      animate('400ms cubic-bezier(0.4, 0, 0.2, 1)', 
        style({ 
          opacity: 1, 
          transform: 'scale(1) translateY(0)' 
        })
      ),
    ], { optional: true })
  ]),
]);

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [CommonModule, RouterModule, RouterOutlet, NotificationsComponent, GlobalLoadingComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [
    trigger('slideInOut', [
      transition(':enter', [
        style({ height: 0, opacity: 0 }),
        animate('200ms ease-out', style({ height: '*', opacity: 1 })),
      ]),
      transition(':leave', [
        animate('200ms ease-in', style({ height: 0, opacity: 0 })),
      ]),
    ]),
    routeAnimations
  ],
  template: `
    <div class="h-screen flex flex-col bg-background transition-theme gradient-mesh overflow-hidden">
      <nav class="glass flex-shrink-0 z-50 border-b border-border/50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="flex justify-between h-16">
            <div class="flex">
              <div class="flex-shrink-0 flex items-center">
                <h1
                  class="text-xl font-bold bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent"
                >
                  PDF Summarizer
                </h1>
              </div>
              <div class="hidden sm:ml-8 sm:flex sm:space-x-2">
                <a
                  routerLink="/app/summarize"
                  routerLinkActive="bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300"
                  class="text-muted-foreground hover:text-foreground hover:bg-muted inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-theme"
                >
                  <svg
                    class="w-4 h-4 mr-2"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                    />
                  </svg>
                  Summarize
                </a>
                <a
                  routerLink="/app/library"
                  routerLinkActive="bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300"
                  class="text-muted-foreground hover:text-foreground hover:bg-muted inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-theme"
                >
                  <svg
                    class="w-4 h-4 mr-2"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2"
                    />
                  </svg>
                  Library
                </a>
                <a
                  routerLink="/app/chat"
                  routerLinkActive="bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300"
                  class="text-muted-foreground hover:text-foreground hover:bg-muted inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-theme"
                >
                  <svg
                    class="w-4 h-4 mr-2"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                    />
                  </svg>
                  Chat
                </a>
              </div>
            </div>
            <div class="flex items-center space-x-4">
              <!-- Mobile menu button -->
              <button
                (click)="toggleMobileMenu()"
                class="sm:hidden p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-theme"
                [attr.aria-label]="
                  isMobileMenuOpen() ? 'Close menu' : 'Open menu'
                "
                [attr.aria-expanded]="isMobileMenuOpen()"
              >
                <svg
                  *ngIf="!isMobileMenuOpen()"
                  class="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                </svg>
                <svg
                  *ngIf="isMobileMenuOpen()"
                  class="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
              <button
                (click)="toggleTheme()"
                class="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-theme"
                [attr.aria-label]="
                  isDarkMode() ? 'Switch to light mode' : 'Switch to dark mode'
                "
              >
                <svg
                  *ngIf="!isDarkMode()"
                  class="w-5 h-5"
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
                  class="w-5 h-5"
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
              <div class="hidden sm:block h-8 w-px bg-border/50"></div>
              <div class="hidden sm:flex items-center space-x-3">
                <div class="flex items-center">
                  <div
                    class="w-8 h-8 rounded-full bg-gradient-to-br from-primary-400 to-accent-400 flex items-center justify-center text-white font-medium text-sm"
                  >
                    {{ currentUser()?.name?.charAt(0)?.toUpperCase() }}
                  </div>
                  <span
                    class="ml-2 text-sm font-medium text-foreground hidden md:block"
                    >{{ currentUser()?.name }}</span
                  >
                </div>
                <button
                  (click)="logout()"
                  class="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-theme"
                >
                  <svg
                    class="w-4 h-4 mr-1.5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                    />
                  </svg>
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Mobile menu -->
        <div
          *ngIf="isMobileMenuOpen()"
          class="sm:hidden border-t border-border/50"
          [@slideInOut]
        >
          <div class="px-4 pt-2 pb-3 space-y-1">
            <a
              routerLink="/app/summarize"
              routerLinkActive="bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300"
              (click)="closeMobileMenu()"
              class="text-muted-foreground hover:text-foreground hover:bg-muted flex items-center px-3 py-2 rounded-lg text-base font-medium transition-theme"
            >
              <svg
                class="w-5 h-5 mr-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                />
              </svg>
              Summarize
            </a>
            <a
              routerLink="/app/library"
              routerLinkActive="bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300"
              (click)="closeMobileMenu()"
              class="text-muted-foreground hover:text-foreground hover:bg-muted flex items-center px-3 py-2 rounded-lg text-base font-medium transition-theme"
            >
              <svg
                class="w-5 h-5 mr-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2"
                />
              </svg>
              Library
            </a>
            <a
              routerLink="/app/chat"
              routerLinkActive="bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300"
              (click)="closeMobileMenu()"
              class="text-muted-foreground hover:text-foreground hover:bg-muted flex items-center px-3 py-2 rounded-lg text-base font-medium transition-theme"
            >
              <svg
                class="w-5 h-5 mr-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
              Chat
            </a>
          </div>
          <div class="border-t border-border/50 px-4 py-3">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center">
                <div
                  class="w-10 h-10 rounded-full bg-gradient-to-br from-primary-400 to-accent-400 flex items-center justify-center text-white font-medium"
                >
                  {{ currentUser()?.name?.charAt(0)?.toUpperCase() }}
                </div>
                <div class="ml-3">
                  <div class="text-base font-medium text-foreground">
                    {{ currentUser()?.name }}
                  </div>
                  <div class="text-sm text-muted-foreground">
                    {{ currentUser()?.email }}
                  </div>
                </div>
              </div>
              <button
                (click)="toggleTheme()"
                class="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-theme"
                [attr.aria-label]="
                  isDarkMode() ? 'Switch to light mode' : 'Switch to dark mode'
                "
              >
                <svg
                  *ngIf="!isDarkMode()"
                  class="w-5 h-5"
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
                  class="w-5 h-5"
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
            <button
              (click)="logout()"
              class="w-full flex items-center px-3 py-2 rounded-lg text-base font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-theme"
            >
              <svg
                class="w-5 h-5 mr-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                />
              </svg>
              Logout
            </button>
          </div>
        </div>
      </nav>

      <main class="relative flex-1 overflow-hidden">
        <div [@routeAnimations]="prepareRoute(outlet) || 'none'" class="h-full">
          <router-outlet #outlet="outlet"></router-outlet>
        </div>
      </main>

      <!-- Global UI Components -->
      <app-notifications></app-notifications>
      <app-global-loading></app-global-loading>
    </div>
  `,
})
export class LayoutComponent {
  private readonly authStore = inject(AuthStore);
  private readonly themeStore = inject(ThemeStore);
  readonly uiStore = inject(UIStore);
  
  // Expose store selectors for template
  readonly currentUser = this.authStore.user;
  readonly isDarkMode = this.themeStore.isDarkMode;
  readonly isMobileMenuOpen = this.uiStore.mobileMenuOpen;

  toggleTheme() {
    this.themeStore.toggleTheme();
  }

  toggleMobileMenu() {
    this.uiStore.toggleMobileMenu();
  }

  closeMobileMenu() {
    this.uiStore.closeMobileMenu();
  }

  logout() {
    this.authStore.logout(undefined);
  }

  prepareRoute(outlet: RouterOutlet) {
    return outlet?.activatedRouteData?.['animation'];
  }
}
