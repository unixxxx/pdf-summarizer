import { Component, inject, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  NonNullableFormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { ModalRef, MODAL_REF } from '../../../core/services/modal';
import { FolderItem } from '../store/state/folder';
import { Tag } from '../../tag/store/state/tag';
import { FolderCreateDto } from '../dtos/folder';
import { ToFormControls } from '../../../core/utils/transform';
import { availableColors } from '../../../core/utils/colors';
import { ChipInput, ChipItem } from '../../../shared/components/chip-input';

@Component({
  selector: 'app-folder-create',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, ChipInput],
  template: `
    <div class="modal-content">
      <div class="modal-header">
        <h2 class="text-xl font-semibold">New Folder</h2>
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

      <form [formGroup]="form" (ngSubmit)="create()" class="modal-body">
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
            <option [value]="null">No parent (root level)</option>
            @for (folder of folders(); track folder.id) {
            <option [value]="folder.id">{{ folder.name }}</option>
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
            [disabled]="form.invalid || isSubmitting"
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
              Creating... } @else { Create Folder }
            </span>
          </button>
        </div>
      </form>
    </div>
  `,
  styles: [],
})
export class FolderCreate {
  private fb = inject(NonNullableFormBuilder);
  private modalRef = inject<ModalRef<FolderCreateDto>>(MODAL_REF);

  parentId = input<string>();
  folders = input<FolderItem[]>([]);
  tags = input<Tag[]>([]);

  form: FormGroup<ToFormControls<FolderCreateDto>> = this.fb.group({
    name: this.fb.control<string>('', [
      Validators.required,
      Validators.minLength(1),
    ]),
    description: this.fb.control<string | undefined>(undefined),
    color: this.fb.control<string>('#6B7280', [Validators.required]),
    parent_id: this.fb.control<string | undefined>(this.parentId()),
    tags: this.fb.control<ChipItem[]>([]),
  });

  isSubmitting = false;

  availableColors = availableColors;

  constructor() {
    this.form.controls.tags.valueChanges.subscribe((value) => {
      console.log(value);
    });
  }

  selectColor(color: string) {
    this.form.patchValue({ color });
  }

  create() {
    if (this.form.valid && !this.isSubmitting) {
      this.isSubmitting = true;
      const formValue = this.form.getRawValue();
      this.modalRef.dismiss(formValue, 'create');
    }
  }

  cancel() {
    this.modalRef.dismiss(undefined, 'cancel');
  }
}
