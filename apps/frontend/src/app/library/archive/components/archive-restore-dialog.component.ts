import {
  Component,
  ChangeDetectionStrategy,
  input,
  output,
} from '@angular/core';

import { trigger, style, transition, animate } from '@angular/animations';

@Component({
  selector: 'app-archive-restore-dialog',
  standalone: true,
  imports: [],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [
    trigger('backdrop', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('200ms ease-out', style({ opacity: 1 })),
      ]),
      transition(':leave', [animate('150ms ease-in', style({ opacity: 0 }))]),
    ]),
    trigger('dialog', [
      transition(':enter', [
        style({ opacity: 0, transform: 'scale(0.95) translateY(10px)' }),
        animate(
          '300ms cubic-bezier(0.4, 0, 0.2, 1)',
          style({ opacity: 1, transform: 'scale(1) translateY(0)' })
        ),
      ]),
      transition(':leave', [
        animate(
          '200ms cubic-bezier(0.4, 0, 0.2, 1)',
          style({ opacity: 0, transform: 'scale(0.95) translateY(10px)' })
        ),
      ]),
    ]),
  ],
  template: `
    @if (show()) {
    <!-- Modal Backdrop -->
    <!-- eslint-disable-next-line @angular-eslint/template/click-events-have-key-events, @angular-eslint/template/interactive-supports-focus -->
    <div
      @backdrop
      class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center"
      (click)="onBackdropClick($event)"
    >
      <!-- Modal Content -->
      <!-- eslint-disable-next-line @angular-eslint/template/click-events-have-key-events, @angular-eslint/template/interactive-supports-focus -->
      <div
        @dialog
        class="bg-background rounded-lg shadow-xl w-full max-w-md mx-4"
        (click)="$event.stopPropagation()"
      >
        <!-- Modal Header -->
        <div class="px-6 py-4 border-b border-border">
          <h3 class="text-lg font-semibold text-foreground">
            {{ isFolder() ? 'Restore Folder' : 'Restore Document' }}
          </h3>
        </div>

        <!-- Modal Body -->
        <div class="px-6 py-4">
          <p class="text-foreground">
            Are you sure you want to restore
            <strong class="font-semibold">"{{ itemName() }}"</strong>
            {{ isFolder() ? 'and all its contents' : '' }}?
          </p>

          <div class="mt-3 p-3 bg-muted/50 border border-muted rounded-lg">
            <p class="text-sm text-muted-foreground">
              <svg
                class="inline w-4 h-4 mr-1"
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
              @if (isFolder()) { This folder and all its contents will be
              restored to
              {{ parentName() ? parentName() : 'the root level' }}. } @else {
              This document will be restored to
              {{ parentName() ? parentName() : 'Unfiled documents' }}. }
            </p>
          </div>

          @if (isFolder() && (documentCount() > 0 || childrenCount() > 0)) {
          <div class="mt-3 text-sm text-muted-foreground">
            <p class="font-medium mb-1">This will restore:</p>
            <ul class="space-y-1 ml-4">
              @if (documentCount() > 0) {
              <li>
                • {{ documentCount() }} document{{
                  documentCount() > 1 ? 's' : ''
                }}
              </li>
              } @if (childrenCount() > 0) {
              <li>
                • {{ childrenCount() }} subfolder{{
                  childrenCount() > 1 ? 's' : ''
                }}
              </li>
              }
            </ul>
          </div>
          }
        </div>

        <!-- Modal Footer -->
        <div class="px-6 py-4 border-t border-border flex justify-end gap-3">
          <button
            type="button"
            (click)="onCancel()"
            class="px-4 py-2 text-sm font-medium text-foreground bg-muted hover:bg-muted/80 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            (click)="onConfirm()"
            class="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
          >
            Restore
          </button>
        </div>
      </div>
    </div>
    }
  `,
})
export class ArchiveRestoreDialogComponent {
  show = input.required<boolean>();
  itemName = input.required<string>();
  isFolder = input.required<boolean>();
  parentName = input<string | null>(null);
  documentCount = input<number>(0);
  childrenCount = input<number>(0);

  confirm = output<void>();
  canceled = output<void>();

  onConfirm() {
    this.confirm.emit();
  }

  onCancel() {
    this.canceled.emit();
  }

  onBackdropClick(event: MouseEvent) {
    // Only close if clicking directly on backdrop
    if (event.target === event.currentTarget) {
      this.onCancel();
    }
  }
}
