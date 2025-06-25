import {
  Component,
  ChangeDetectionStrategy,
  inject,
  input,
} from '@angular/core';
import { MODAL_REF } from '../../../core/services/modal';
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
    <!-- Modal Content -->
    <div
      @dialog
      class="relative bg-card rounded-xl shadow-xl max-w-md w-full mx-4"
    >
      <!-- Modal Header -->
      <div class="flex items-center justify-between p-6 pb-4">
        <h2 class="text-xl font-semibold text-foreground">Empty Archive</h2>
      </div>

      <!-- Modal Body -->
      <div class="px-6 pb-6">
        <div
          class="flex items-center gap-3 p-3 bg-error/10 border border-error/20 rounded-lg mb-4"
        >
          <svg
            class="w-5 h-5 text-error flex-shrink-0"
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
          <p class="text-sm text-error font-medium">
            This action cannot be undone
          </p>
        </div>

        <p class="text-foreground mb-4">
          Are you sure you want to permanently delete all items in the archive?
        </p>

        @if (documentCount() > 0 || folderCount() > 0) {
        <div class="bg-muted/50 rounded-lg p-3 text-sm text-muted-foreground">
          <p class="mb-2">This will permanently delete:</p>
          <ul class="list-disc list-inside space-y-1">
            @if (documentCount() > 0) {
            <li>
              {{ documentCount() }}
              {{ documentCount() === 1 ? 'document' : 'documents' }}
            </li>
            } @if (folderCount() > 0) {
            <li>
              {{ folderCount() }}
              {{ folderCount() === 1 ? 'folder' : 'folders' }}
            </li>
            } @if (totalSize() > 0) {
            <li>{{ formatFileSize(totalSize()) }} of data</li>
            }
          </ul>
        </div>
        }
      </div>

      <!-- Modal Footer -->
      <div
        class="flex items-center justify-end gap-3 px-6 py-4 bg-muted/30 rounded-b-xl"
      >
        <button
          (click)="cancel()"
          class="px-4 py-2 text-sm font-medium text-foreground hover:bg-muted rounded-lg transition-colors"
        >
          Cancel
        </button>
        <button
          (click)="confirm()"
          class="px-4 py-2 text-sm font-medium text-white bg-error hover:bg-error/90 rounded-lg transition-colors"
        >
          Empty Archive
        </button>
      </div>
    </div>
  `,
})
export class ArchiveEmptyDialog {
  private modalRef = inject(MODAL_REF);

  documentCount = input<number>(0);
  folderCount = input<number>(0);
  totalSize = input<number>(0);

  formatFileSize = formatFileSize;

  confirm() {
    this.modalRef.dismiss(true);
  }

  cancel() {
    this.modalRef.dismiss(false);
  }
}
