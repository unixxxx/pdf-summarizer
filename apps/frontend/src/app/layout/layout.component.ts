import { Component, inject, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { trigger, state, style, transition, animate } from '@angular/animations';
import { AuthService } from '../auth.service';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [CommonModule, RouterModule],
  animations: [
    trigger('slideInOut', [
      transition(':enter', [
        style({ height: 0, opacity: 0 }),
        animate('200ms ease-out', style({ height: '*', opacity: 1 }))
      ]),
      transition(':leave', [
        animate('200ms ease-in', style({ height: 0, opacity: 0 }))
      ])
    ])
  ],
  template: `
    <div class="min-h-screen bg-background transition-theme gradient-mesh">
      <nav class="glass sticky top-0 z-50 border-b border-border/50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="flex justify-between h-16">
            <div class="flex">
              <div class="flex-shrink-0 flex items-center">
                <h1 class="text-xl font-bold bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">
                  PDF Summarizer
                </h1>
              </div>
              <div class="hidden sm:ml-8 sm:flex sm:space-x-2">
                <a routerLink="/app/upload" 
                   routerLinkActive="bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300" 
                   class="text-muted-foreground hover:text-foreground hover:bg-muted inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-theme">
                  <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  Upload PDF
                </a>
                <a routerLink="/app/text" 
                   routerLinkActive="bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300"
                   class="text-muted-foreground hover:text-foreground hover:bg-muted inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-theme">
                  <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Text
                </a>
                <a routerLink="/app/history" 
                   routerLinkActive="bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300"
                   class="text-muted-foreground hover:text-foreground hover:bg-muted inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-theme">
                  <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  History
                </a>
              </div>
            </div>
            <div class="flex items-center space-x-4">
              <!-- Mobile menu button -->
              <button (click)="toggleMobileMenu()" 
                      class="sm:hidden p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-theme"
                      [attr.aria-label]="isMobileMenuOpen() ? 'Close menu' : 'Open menu'"
                      [attr.aria-expanded]="isMobileMenuOpen()">
                <svg *ngIf="!isMobileMenuOpen()" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
                <svg *ngIf="isMobileMenuOpen()" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              <button (click)="toggleTheme()" 
                      class="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-theme"
                      [attr.aria-label]="isDarkMode() ? 'Switch to light mode' : 'Switch to dark mode'">
                <svg *ngIf="!isDarkMode()" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
                <svg *ngIf="isDarkMode()" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </button>
              <div class="hidden sm:block h-8 w-px bg-border/50"></div>
              <div class="hidden sm:flex items-center space-x-3">
                <div class="flex items-center">
                  <div class="w-8 h-8 rounded-full bg-gradient-to-br from-primary-400 to-accent-400 flex items-center justify-center text-white font-medium text-sm">
                    {{ currentUser()?.name?.charAt(0)?.toUpperCase() }}
                  </div>
                  <span class="ml-2 text-sm font-medium text-foreground hidden md:block">{{ currentUser()?.name }}</span>
                </div>
                <button (click)="logout()" 
                        class="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-theme">
                  <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Mobile menu -->
        <div *ngIf="isMobileMenuOpen()" 
             class="sm:hidden border-t border-border/50"
             [@slideInOut]>
          <div class="px-4 pt-2 pb-3 space-y-1">
            <a routerLink="/app/upload" 
               routerLinkActive="bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300"
               (click)="closeMobileMenu()"
               class="text-muted-foreground hover:text-foreground hover:bg-muted flex items-center px-3 py-2 rounded-lg text-base font-medium transition-theme">
              <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              Upload PDF
            </a>
            <a routerLink="/app/text" 
               routerLinkActive="bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300"
               (click)="closeMobileMenu()"
               class="text-muted-foreground hover:text-foreground hover:bg-muted flex items-center px-3 py-2 rounded-lg text-base font-medium transition-theme">
              <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Text
            </a>
            <a routerLink="/app/history" 
               routerLinkActive="bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300"
               (click)="closeMobileMenu()"
               class="text-muted-foreground hover:text-foreground hover:bg-muted flex items-center px-3 py-2 rounded-lg text-base font-medium transition-theme">
              <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              History
            </a>
          </div>
          <div class="border-t border-border/50 px-4 py-3">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center">
                <div class="w-10 h-10 rounded-full bg-gradient-to-br from-primary-400 to-accent-400 flex items-center justify-center text-white font-medium">
                  {{ currentUser()?.name?.charAt(0)?.toUpperCase() }}
                </div>
                <div class="ml-3">
                  <div class="text-base font-medium text-foreground">{{ currentUser()?.name }}</div>
                  <div class="text-sm text-muted-foreground">{{ currentUser()?.email }}</div>
                </div>
              </div>
              <button (click)="toggleTheme()" 
                      class="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-theme"
                      [attr.aria-label]="isDarkMode() ? 'Switch to light mode' : 'Switch to dark mode'">
                <svg *ngIf="!isDarkMode()" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
                <svg *ngIf="isDarkMode()" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </button>
            </div>
            <button (click)="logout()" 
                    class="w-full flex items-center px-3 py-2 rounded-lg text-base font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-theme">
              <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Logout
            </button>
          </div>
        </div>
      </nav>
      
      <main class="animate-fade-in">
        <router-outlet></router-outlet>
      </main>
    </div>
  `
})
export class LayoutComponent {
  private authService = inject(AuthService);
  currentUser = this.authService.currentUser;
  isDarkMode = signal(false);
  isMobileMenuOpen = signal(false);
  
  constructor() {
    // Check for saved theme preference or default to light mode
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    this.isDarkMode.set(savedTheme === 'dark' || (!savedTheme && prefersDark));
    
    // Apply theme on component initialization
    effect(() => {
      if (this.isDarkMode()) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    });
  }
  
  toggleTheme() {
    this.isDarkMode.update(dark => !dark);
    localStorage.setItem('theme', this.isDarkMode() ? 'dark' : 'light');
  }
  
  toggleMobileMenu() {
    this.isMobileMenuOpen.update(open => !open);
  }
  
  closeMobileMenu() {
    this.isMobileMenuOpen.set(false);
  }
  
  logout() {
    this.authService.logout().subscribe();
  }
}