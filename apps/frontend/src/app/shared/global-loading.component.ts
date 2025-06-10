import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { trigger, transition, style, animate } from '@angular/animations';
import { UIStore } from './ui.store';

@Component({
  selector: 'app-global-loading',
  standalone: true,
  imports: [CommonModule],
  animations: [
    trigger('fadeIn', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('200ms ease-out', style({ opacity: 1 })),
      ]),
      transition(':leave', [
        animate('200ms ease-in', style({ opacity: 0 })),
      ]),
    ]),
  ],
  template: `
    @if (globalLoading()) {
    <div
      class="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
      [@fadeIn]
    >
      <div class="text-center animate-fade-in">
        <div class="relative mx-auto w-24 h-24 mb-6">
          <div
            class="absolute inset-0 rounded-full border-4 border-muted animate-pulse-soft"
          ></div>
          <div
            class="absolute inset-0 rounded-full border-4 border-primary-600 border-t-transparent animate-spin"
          ></div>
        </div>
        @if (globalLoadingMessage()) {
        <h2 class="text-xl font-semibold text-foreground mb-2">
          {{ globalLoadingMessage() }}
        </h2>
        }
        <p class="text-muted-foreground">Please wait...</p>
      </div>
    </div>
    }
  `,
})
export class GlobalLoadingComponent {
  private readonly uiStore = inject(UIStore);

  readonly globalLoading = this.uiStore.globalLoading;
  readonly globalLoadingMessage = this.uiStore.globalLoadingMessage;
}