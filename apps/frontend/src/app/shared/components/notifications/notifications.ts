import { Component, inject } from '@angular/core';

import { trigger, transition, style, animate } from '@angular/animations';
import { UIStore } from '../../ui.store';

@Component({
  selector: 'app-notifications',
  standalone: true,
  imports: [],
  animations: [
    trigger('slideIn', [
      transition(':enter', [
        style({ transform: 'translateX(100%)', opacity: 0 }),
        animate(
          '200ms ease-out',
          style({ transform: 'translateX(0)', opacity: 1 })
        ),
      ]),
      transition(':leave', [
        animate(
          '200ms ease-in',
          style({ transform: 'translateX(100%)', opacity: 0 })
        ),
      ]),
    ]),
  ],
  template: `
    <div class="fixed top-20 right-4 z-50 space-y-2 max-w-sm">
      @for (notification of notifications(); track notification.id) {
      <div
        [@slideIn]
        class="glass rounded-lg p-4 shadow-lg flex items-start gap-3"
        [class.border-success-500]="notification.type === 'success'"
        [class.border-error-500]="notification.type === 'error'"
        [class.border-warning-500]="notification.type === 'warning'"
        [class.border-info-500]="notification.type === 'info'"
        [class.border-l-4]="true"
      >
        <!-- Icon -->
        <div class="flex-shrink-0">
          @switch (notification.type) { @case ('success') {
          <svg
            class="w-5 h-5 text-success-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          } @case ('error') {
          <svg
            class="w-5 h-5 text-error"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          } @case ('warning') {
          <svg
            class="w-5 h-5 text-warning-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          } @default {
          <svg
            class="w-5 h-5 text-info-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          } }
        </div>

        <!-- Content -->
        <div class="flex-1">
          <p class="text-sm text-foreground">{{ notification.message }}</p>
        </div>

        <!-- Close button -->
        <button
          (click)="removeNotification(notification.id)"
          class="flex-shrink-0 p-1 rounded hover:bg-muted/50 transition-colors"
        >
          <svg
            class="w-4 h-4 text-muted-foreground"
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
      </div>
      }
    </div>
  `,
})
export class Notifications {
  private readonly uiStore = inject(UIStore);

  readonly notifications = this.uiStore.notifications;

  removeNotification(id: string): void {
    this.uiStore.removeNotification(id);
  }
}
