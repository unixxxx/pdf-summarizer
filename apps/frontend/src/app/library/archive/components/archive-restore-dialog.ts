import {
  Component,
  ChangeDetectionStrategy,
  inject,
  input,
} from '@angular/core';
import { MODAL_REF } from '../../../core/services/modal';
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
    <!-- Modal Content -->
    <div
      @dialog
      class="relative bg-card rounded-xl shadow-xl max-w-md w-full mx-4"
    >
      <!-- Modal Header -->
      <div class="flex items-center justify-between p-6 pb-4">
        <h2 class="text-xl font-semibold text-foreground">
          Restore {{ isFolder() ? 'Folder' : 'Document' }}
        </h2>
      </div>

      <!-- Modal Body -->
      <div class="px-6 pb-6">
        <p class="text-foreground mb-4">
          Are you sure you want to restore
          <span class="font-semibold">{{ itemName() }}</span
          >?
        </p>

        @if (isFolder()) {
        <div class="bg-muted/50 rounded-lg p-3 text-sm text-muted-foreground">
          <p class="mb-2">This folder contains:</p>
          <ul class="list-disc list-inside space-y-1">
            @if (documentCount() > 0) {
            <li>
              {{ documentCount() }}
              {{ documentCount() === 1 ? 'document' : 'documents' }}
            </li>
            } @if (childrenCount() > 0) {
            <li>
              {{ childrenCount() }}
              {{ childrenCount() === 1 ? 'subfolder' : 'subfolders' }}
            </li>
            }
          </ul>
          <p class="mt-2">All contents will be restored.</p>
        </div>
        } @if (parentName()) {
        <p class="text-sm text-muted-foreground mt-3">
          @if (isFolder()) { This folder will be restored to the root level. }
          @else { This document will be restored to the root level. }
        </p>
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
          class="px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary/90 rounded-lg transition-colors"
        >
          Restore
        </button>
      </div>
    </div>
  `,
})
export class ArchiveRestoreDialog {
  private modalRef = inject(MODAL_REF);

  itemName = input.required<string>();
  isFolder = input.required<boolean>();
  parentName = input<string | null>(null);
  documentCount = input<number>(0);
  childrenCount = input<number>(0);

  confirm() {
    this.modalRef.dismiss(true);
  }

  cancel() {
    this.modalRef.dismiss(false);
  }
}
