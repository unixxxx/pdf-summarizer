import {
  Component,
  ChangeDetectionStrategy,
  input,
  output,
} from '@angular/core';

import { trigger, style, transition, animate } from '@angular/animations';
import { formatFileSize } from '../../../core/utils/file-size.formatter';

@Component({
  selector: 'app-archive-empty-dialog',
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
          <h3 class="text-lg font-semibold text-foreground">Empty Archive</h3>
        </div>

        <!-- Modal Body -->
        <div class="px-6 py-4">
          <p class="text-foreground">
            Are you sure you want to permanently delete all items in archive?
          </p>

          <div class="mt-4 p-4 bg-error/10 border border-error/20 rounded-lg">
            <div class="flex items-start">
              <svg
                class="w-5 h-5 text-error mt-0.5 mr-3 flex-shrink-0"
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
              <div class="text-sm">
                <p class="text-error font-semibold mb-2">
                  This action cannot be undone!
                </p>
                <p class="text-error/90">
                  All items in archive will be permanently deleted and cannot be
                  recovered.
                </p>
              </div>
            </div>
          </div>

          @if (documentCount() > 0 || folderCount() > 0) {
          <div
            class="mt-4 p-3 bg-muted/50 border border-muted rounded-lg text-sm"
          >
            <p class="font-medium text-foreground mb-2">
              You are about to permanently delete:
            </p>
            <ul class="space-y-1 text-muted-foreground">
              @if (documentCount() > 0) {
              <li>
                • {{ documentCount() }} document{{
                  documentCount() > 1 ? 's' : ''
                }}
              </li>
              } @if (folderCount() > 0) {
              <li>
                • {{ folderCount() }} folder{{ folderCount() > 1 ? 's' : '' }}
              </li>
              } @if (totalSize() > 0) {
              <li>• {{ formatFileSize(totalSize()) }} of data</li>
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
            class="px-4 py-2 text-sm font-medium text-white bg-error hover:bg-error/90 rounded-lg transition-colors"
          >
            Empty Archive
          </button>
        </div>
      </div>
    </div>
    }
  `,
})
export class ArchiveEmptyDialogComponent {
  show = input.required<boolean>();
  documentCount = input<number>(0);
  folderCount = input<number>(0);
  totalSize = input<number>(0);

  confirm = output<void>();
  canceled = output<void>();

  formatFileSize = formatFileSize;

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
