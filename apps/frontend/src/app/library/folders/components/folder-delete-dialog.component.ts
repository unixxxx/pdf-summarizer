import { Component, inject, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { trigger, style, transition, animate } from '@angular/animations';
import { LibraryStore } from '../../library.store';

@Component({
  selector: 'app-folder-delete-dialog',
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
    @if (libraryStore.showDeleteFolderConfirm() && libraryStore.deletingFolder()) {
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
            <h3 class="text-lg font-semibold text-foreground">Move Folder to Trash</h3>
          </div>

          <!-- Modal Body -->
          <div class="px-6 py-4">
            <p class="text-foreground">
              Are you sure you want to delete the folder
              <strong class="font-semibold">"{{ libraryStore.deletingFolder()?.name }}"</strong>?
            </p>
            
            <div class="mt-4 p-4 bg-warning/10 border border-warning/20 rounded-lg">
              <div class="flex items-start">
                <svg class="w-5 h-5 text-warning mt-0.5 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                <div class="text-sm">
                  <p class="text-warning font-semibold mb-2">
                    This will move to trash:
                  </p>
                  <ul class="space-y-1 text-warning/90">
                    <li>• The selected folder and all its contents</li>
                    <li>• Any subfolders within this folder</li>
                    <li>• All documents within this folder and its subfolders</li>
                  </ul>
                  <p class="mt-3 text-warning/80 text-xs">
                    You can restore items from the trash within 30 days.
                  </p>
                </div>
              </div>
            </div>
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
              class="px-4 py-2 text-sm font-medium text-white bg-warning hover:bg-warning/90 rounded-lg transition-colors"
            >
              Move to Trash
            </button>
          </div>
        </div>
      </div>
    }
  `,
})
export class FolderDeleteDialogComponent {
  protected libraryStore = inject(LibraryStore);

  onConfirm() {
    this.libraryStore.executeDeleteFolder();
  }

  onCancel() {
    this.libraryStore.cancelDeleteFolder();
  }

  onBackdropClick(event: MouseEvent) {
    // Only close if clicking directly on backdrop
    if (event.target === event.currentTarget) {
      this.onCancel();
    }
  }
}