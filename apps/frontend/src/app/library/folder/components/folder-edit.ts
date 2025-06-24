import { Component, inject, input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormGroup,
  NonNullableFormBuilder,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { ModalRef, MODAL_REF } from '../../../core/services/modal';
import { FolderItem } from '../store/state/folder';
import { Tag } from '../../tag/store/state/tag';
import { FolderUpdateDto } from '../dtos/folder';
import { ToFormControls } from '../../../core/utils/transform';
import { FormatDatePipe } from '../../../core/pipes/formatDate';
import { availableColors } from '../../../core/utils/colors';
import { ChipInput, ChipItem } from '../../../shared/components/chip-input';

@Component({
  selector: 'app-folder-edit',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormatDatePipe, ChipInput],
  template: `
    <div class="modal-content">
      <div class="modal-header">
        <h2 class="text-xl font-semibold">Edit Folder</h2>
        <button
          type="button"
          class="p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
          (click)="cancel()"
          aria-label="Close"
        >
          <svg
            class="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            ></path>
          </svg>
        </button>
      </div>

      <form [formGroup]="form" (ngSubmit)="save()" class="modal-body">
        <div class="mb-6">
          <label
            for="name"
            class="block mb-2 text-sm font-medium text-foreground"
            >Name</label
          >
          <input
            id="name"
            type="text"
            [formControl]="form.controls.name"
            class="w-full px-3 py-2 text-sm border border-border rounded-md bg-background text-foreground transition-colors focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500/10"
            placeholder="Enter folder name"
            autocomplete="off"
          />
          @if (form.get('name')?.invalid && form.get('name')?.touched) {
          <span class="mt-1 text-xs text-error">Folder name is required</span>
          }
        </div>

        <div class="mb-6">
          <label
            for="description"
            class="block mb-2 text-sm font-medium text-foreground"
            >Description</label
          >
          <textarea
            id="description"
            [formControl]="form.controls.description"
            class="w-full px-3 py-2 text-sm border border-border rounded-md bg-background text-foreground transition-colors focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500/10"
            rows="3"
            placeholder="Enter folder description (optional)"
          ></textarea>
        </div>

        <div class="mb-6">
          <span class="block mb-2 text-sm font-medium text-foreground"
            >Color</span
          >
          <div
            class="flex flex-wrap gap-2"
            role="group"
            aria-label="Select folder color"
          >
            @for (color of availableColors; track color) {
            <button
              type="button"
              class="w-10 h-10 rounded-md border-2 transition-all hover:scale-110"
              [class.border-transparent]="form.get('color')?.value !== color"
              [class.border-foreground]="form.get('color')?.value === color"
              [class.shadow-lg]="form.get('color')?.value === color"
              [class.ring-2]="form.get('color')?.value === color"
              [class.ring-offset-2]="form.get('color')?.value === color"
              [class.ring-offset-background]="
                form.get('color')?.value === color
              "
              [class.ring-foreground]="form.get('color')?.value === color"
              [style.background-color]="color"
              (click)="selectColor(color)"
              [attr.aria-label]="'Select color ' + color"
            ></button>
            }
          </div>
        </div>

        <div class="mb-6">
          <label
            for="parentId"
            class="block mb-2 text-sm font-medium text-foreground"
            >Parent Folder</label
          >
          <select
            id="parentId"
            [formControl]="form.controls.parent_id"
            class="w-full px-3 py-2 pr-10 text-sm border border-border rounded-md bg-background text-foreground transition-colors focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500/10"
          >
            <option [ngValue]="null">No parent (root level)</option>
            @for (folder of validParentFolders; track folder.id) {
            <option [ngValue]="folder.id">{{ folder.name }}</option>
            }
          </select>
        </div>

        <div class="mb-6">
          <label
            for="tags"
            class="block mb-2 text-sm font-medium text-foreground"
            >Tags</label
          >
          <app-chip-input
            [formControl]="form.controls.tags"
            [suggestions]="tags()"
            placeholder="Select tags..."
          />
        </div>

        @if (folder()) {
        <div class="p-4 mb-6 bg-muted/30 border border-border rounded-md">
          <div class="flex justify-between items-center py-1 text-sm">
            <span class="text-muted-foreground">Documents:</span>
            <span class="font-medium text-foreground">{{
              folder().documentCount || 0
            }}</span>
          </div>
          @if (folder().children && folder().children.length > 0) {
          <div class="flex justify-between items-center py-1 text-sm">
            <span class="text-muted-foreground">Subfolders:</span>
            <span class="font-medium text-foreground">{{
              folder().children.length
            }}</span>
          </div>
          } @if (folder().createdAt) {
          <div class="flex justify-between items-center py-1 text-sm">
            <span class="text-muted-foreground">Created:</span>
            <span class="font-medium text-foreground">{{
              folder().createdAt | formatDate
            }}</span>
          </div>
          } @if (folder().updatedAt && folder().updatedAt !==
          folder().createdAt) {
          <div class="flex justify-between items-center py-1 text-sm">
            <span class="text-muted-foreground">Updated:</span>
            <span class="font-medium text-foreground">{{
              folder().updatedAt | formatDate
            }}</span>
          </div>
          }
        </div>
        }

        <div class="modal-footer">
          <button
            type="button"
            class="px-4 py-2 text-sm font-medium text-foreground bg-background border border-border rounded-md hover:bg-muted/50 transition-colors"
            (click)="cancel()"
          >
            Cancel
          </button>
          <button
            type="submit"
            class="px-4 py-2 text-sm font-medium text-white bg-primary-500 rounded-md hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            [disabled]="form.invalid || !form.dirty || isSubmitting"
          >
            <span class="flex items-center gap-2">
              @if (isSubmitting) {
              <svg
                class="animate-spin h-4 w-4"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                ></circle>
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Saving... } @else { Save Changes }
            </span>
          </button>
        </div>
      </form>
    </div>
  `,
  styles: [],
})
export class FolderEdit implements OnInit {
  private fb = inject(NonNullableFormBuilder);
  private modalRef = inject<ModalRef<FolderUpdateDto>>(MODAL_REF);

  folder = input.required<FolderItem>();
  folders = input<FolderItem[]>([]);
  tags = input<Tag[]>([]);
  form: FormGroup<ToFormControls<FolderUpdateDto>> = this.fb.group({
    name: this.fb.control<string>('', [
      Validators.required,
      Validators.minLength(1),
    ]),
    description: this.fb.control<string | undefined>(undefined),
    color: this.fb.control<string>('#6B7280', [Validators.required]),
    parent_id: this.fb.control<string | undefined>(undefined),
    tags: this.fb.control<ChipItem[]>([]),
  });

  isSubmitting = false;

  availableColors = availableColors;

  // Get valid parent folders (exclude self and descendants)
  get validParentFolders(): FolderItem[] {
    const currentFolder = this.folder();
    const allFolders = this.folders();

    // Get all descendant IDs
    const descendantIds = new Set<string>();
    const collectDescendants = (folder: FolderItem) => {
      descendantIds.add(folder.id);
      if (folder.children) {
        folder.children.forEach((child) => collectDescendants(child));
      }
    };

    // Find the current folder in the tree to get its descendants
    const findAndCollect = (folders: FolderItem[]) => {
      for (const folder of folders) {
        if (folder.id === currentFolder.id) {
          collectDescendants(folder);
          return;
        }
        if (folder.children) {
          findAndCollect(folder.children);
        }
      }
    };

    // Start from the original folder structure
    findAndCollect(allFolders);

    // Flatten all folders for the dropdown - keep original folder objects with formatted names
    const flattenFolders = (folders: FolderItem[], level = 0): FolderItem[] => {
      const result: FolderItem[] = [];
      for (const folder of folders) {
        // Only include if not a descendant
        if (!descendantIds.has(folder.id)) {
          const prefix = level > 0 ? '\u00A0\u00A0'.repeat(level) + '└─ ' : '';
          // Create a new object but preserve the original ID and other properties
          result.push({
            ...folder,
            // Add prefix to the name for display in dropdown
            name: prefix + folder.name,
            // Ensure we keep the original ID for proper selection
            id: folder.id,
          });
        }
        if (folder.children && folder.children.length > 0) {
          result.push(...flattenFolders(folder.children, level + 1));
        }
      }
      return result;
    };

    return flattenFolders(allFolders);
  }

  ngOnInit() {
    const folderData = this.folder();

    this.form.patchValue({
      name: folderData.name,
      description: folderData.description || '',
      color: folderData.color || '#6B7280',
      parent_id: folderData.parentId,
      tags:
        folderData.tags.map((tag) => ({
          id: tag.id,
          name: tag.name,
          color: tag.color,
        })) || [],
    });
  }

  selectColor(color: string) {
    this.form.patchValue({ color });
    this.form.controls.color.markAsDirty();
  }

  save() {
    if (this.form.valid && this.form.dirty && !this.isSubmitting) {
      this.isSubmitting = true;
      const formValue = this.form.getRawValue();
      this.modalRef.dismiss(formValue, 'update');
    }
  }

  cancel() {
    this.modalRef.dismiss(undefined, 'cancel');
  }
}
