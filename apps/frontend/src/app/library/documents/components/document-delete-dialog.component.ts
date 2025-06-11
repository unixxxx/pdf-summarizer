import { Component, inject, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { trigger, style, transition, animate } from '@angular/animations';
import { LibraryStore } from '../../library.store';

@Component({
  selector: 'app-document-delete-dialog',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [
    trigger('backdrop', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('200ms ease-out', style({ opacity: 1 }))
      ]),
      transition(':leave', [
        animate('150ms ease-in', style({ opacity: 0 }))
      ])
    ]),
    trigger('dialog', [
      transition(':enter', [
        style({ opacity: 0, transform: 'scale(0.95) translateY(10px)' }),
        animate('300ms cubic-bezier(0.4, 0, 0.2, 1)', style({ opacity: 1, transform: 'scale(1) translateY(0)' }))
      ]),
      transition(':leave', [
        animate('200ms cubic-bezier(0.4, 0, 0.2, 1)', style({ opacity: 0, transform: 'scale(0.95) translateY(10px)' }))
      ])
    ])
  ],
  template: `
    @if (libraryStore.showDeleteDocumentConfirm() && libraryStore.deletingDocument()) {
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
            <h3 class="text-lg font-semibold text-foreground">Move to Trash</h3>
          </div>

          <!-- Modal Body -->
          <div class="px-6 py-4">
            <p class="text-foreground">
              Are you sure you want to move
              <strong class="font-semibold">"{{ libraryStore.deletingDocument()?.filename }}"</strong>
              to trash?
            </p>
            
            <div class="mt-3 p-3 bg-muted/50 border border-muted rounded-lg">
              <p class="text-sm text-muted-foreground">
                <svg class="inline w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                The document will be moved to trash where you can restore it later if needed.
              </p>
            </div>

            @if (libraryStore.deletingDocument()?.summary?.tags && libraryStore.deletingDocument()!.summary.tags.length > 0) {
              <div class="mt-3">
                <p class="text-sm text-muted-foreground">
                  This document has {{ libraryStore.deletingDocument()!.summary.tags.length }} tag(s) associated with it.
                </p>
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
              Move to Trash
            </button>
          </div>
        </div>
      </div>
    }
  `,
})
export class DocumentDeleteDialogComponent {
  protected libraryStore = inject(LibraryStore);

  onConfirm() {
    this.libraryStore.executeDeleteDocument();
  }

  onCancel() {
    this.libraryStore.cancelDeleteDocument();
  }

  onBackdropClick(event: MouseEvent) {
    // Only close if clicking directly on backdrop
    if (event.target === event.currentTarget) {
      this.onCancel();
    }
  }
}