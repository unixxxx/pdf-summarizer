import {
  Component,
  inject,
  ChangeDetectionStrategy,
  effect,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { trigger, style, transition, animate } from '@angular/animations';
import { LibraryStore } from '../../library.store';
import { FolderWithChildren } from '../folder.model';

@Component({
  selector: 'app-folder-dialog',
  standalone: true,
  imports: [CommonModule, FormsModule],
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
    @if (libraryStore.showFolderDialog()) {
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
              {{ libraryStore.editingFolder() ? 'Edit Folder' : 'New Folder' }}
            </h3>
          </div>

          <!-- Modal Body -->
          <form (ngSubmit)="onSubmit()" #folderForm="ngForm">
            <div class="px-6 py-4 space-y-4">
              <!-- Folder Name -->
              <div>
                <label
                  for="folderName"
                  class="block text-sm font-medium text-foreground mb-1"
                >
                  Folder Name
                </label>
                <input
                  id="folderName"
                  type="text"
                  [(ngModel)]="name"
                  name="name"
                  required
                  class="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Enter folder name"
                  autocomplete="off"
                />
              </div>

              <!-- Folder Description -->
              <div>
                <label
                  for="folderDescription"
                  class="block text-sm font-medium text-foreground mb-1"
                >
                  Description (optional)
                </label>
                <textarea
                  id="folderDescription"
                  [(ngModel)]="description"
                  name="description"
                  rows="3"
                  class="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Enter folder description"
                ></textarea>
              </div>

              <!-- Parent Folder -->
              <div>
                <label
                  for="parentFolder"
                  class="block text-sm font-medium text-foreground mb-1"
                >
                  Parent Folder (optional)
                </label>
                <select
                  id="parentFolder"
                  [(ngModel)]="parentId"
                  name="parentId"
                  class="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option [ngValue]="null">Root (No parent)</option>
                  @for (folder of getAvailableFolders(); track folder.id) {
                    <option [ngValue]="folder.id">
                      {{ getFolderPath(folder) }}
                    </option>
                  }
                </select>
              </div>

              <!-- Color Picker -->
              <div>
                <p class="block text-sm font-medium text-foreground mb-2">
                  Folder Color
                </p>
                <div class="flex gap-2 flex-wrap" role="group" aria-label="Select folder color">
                  @for (availableColor of libraryStore.availableColors(); track availableColor) {
                    <button
                      type="button"
                      (click)="selectColor(availableColor)"
                      [class.ring-2]="color === availableColor"
                      [class.ring-primary-500]="color === availableColor"
                      [class.ring-offset-2]="color === availableColor"
                      class="w-8 h-8 rounded-full transition-all"
                      [style.background-color]="availableColor"
                      [attr.aria-label]="'Select color ' + availableColor"
                    ></button>
                  }
                </div>
              </div>
            </div>

            <!-- Modal Footer -->
            <div
              class="px-6 py-4 border-t border-border flex justify-end gap-3"
            >
              <button
                type="button"
                (click)="onCancel()"
                class="px-4 py-2 text-sm font-medium text-foreground bg-muted hover:bg-muted/80 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                [disabled]="!folderForm.form.valid"
                class="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:bg-primary-400 disabled:cursor-not-allowed rounded-lg transition-colors"
              >
                {{ libraryStore.editingFolder() ? 'Update' : 'Create' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    }
  `,
})
export class FolderDialogComponent {
  protected libraryStore = inject(LibraryStore);

  // Form fields
  name = '';
  description = '';
  color = '#6B7280';
  parentId: string | null | undefined = null;

  constructor() {
    // Sync form values with store when dialog opens
    effect(() => {
      if (this.libraryStore.showFolderDialog()) {
        const form = this.libraryStore.folderForm();
        const editing = this.libraryStore.editingFolder();
        this.name = form.name || '';
        this.description = form.description || '';
        this.color = form.color || '#6B7280';
        this.parentId = form.parentId || editing?.parentId || editing?.parent_id || null;
      }
    });
  }

  selectColor(color: string) {
    this.color = color;
    // Don't update the store form here, just keep it local
  }

  onSubmit() {
    if (this.name.trim()) {
      this.libraryStore.updateFolderForm({
        name: this.name.trim(),
        description: this.description.trim(),
        color: this.color,
        parentId: this.parentId,
      });
      this.libraryStore.saveFolder();
    }
  }

  getAvailableFolders(): FolderWithChildren[] {
    const editingId = this.libraryStore.editingFolder()?.id;
    return this.flattenFolders(this.libraryStore.folders()).filter(
      folder => {
        // Can't select itself or its descendants as parent
        if (editingId) {
          return folder.id !== editingId && !this.isDescendantOf(folder, editingId);
        }
        return true;
      }
    );
  }

  private flattenFolders(folders: FolderWithChildren[]): FolderWithChildren[] {
    const result: FolderWithChildren[] = [];
    const traverse = (items: FolderWithChildren[]) => {
      for (const item of items) {
        result.push(item);
        if (item.children && item.children.length > 0) {
          traverse(item.children);
        }
      }
    };
    traverse(folders);
    return result;
  }

  private isDescendantOf(folder: FolderWithChildren, ancestorId: string): boolean {
    let current: FolderWithChildren | undefined = folder;
    while (current) {
      const parentId = current.parentId || current.parent_id;
      if (parentId === ancestorId) {
        return true;
      }
      current = this.findFolderById(parentId);
    }
    return false;
  }

  private findFolderById(id: string | null | undefined): FolderWithChildren | undefined {
    if (!id) return undefined;
    const allFolders = this.flattenFolders(this.libraryStore.folders());
    return allFolders.find(f => f.id === id);
  }

  getFolderPath(folder: FolderWithChildren): string {
    const path: string[] = [folder.name];
    let current = folder;
    while (current.parentId || current.parent_id) {
      const parentId = current.parentId || current.parent_id;
      const parent = this.findFolderById(parentId);
      if (parent) {
        path.unshift(parent.name);
        current = parent;
      } else {
        break;
      }
    }
    return path.join(' / ');
  }

  onCancel() {
    this.libraryStore.closeFolderDialog();
  }

  onBackdropClick(event: MouseEvent) {
    // Only close if clicking directly on backdrop
    if (event.target === event.currentTarget) {
      this.onCancel();
    }
  }
}