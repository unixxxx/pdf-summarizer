import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Store } from '@ngrx/store';
import { UploadActions } from '../store/upload.actions';
import { uploadFeature } from '../store/upload.feature';
import { MODAL_REF } from '../../../core/services/modal/modal-ref';
import { ModalRef } from '../../../core/services/modal/modal.types';
import { NgClass } from '@angular/common';

@Component({
  selector: 'app-upload-dialog',
  standalone: true,
  imports: [FormsModule, NgClass],
  template: `
    <div
      class="modal-content bg-card border border-border rounded-xl shadow-2xl w-full animate-scale-in flex flex-col"
      style="height: 700px; max-height: calc(100vh - 2rem);"
      (keydown.escape)="close()"
      tabindex="0"
      role="dialog"
      [attr.aria-modal]="true"
      [attr.aria-labelledby]="'dialog-title'"
    >
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b border-border">
        <h2 id="dialog-title" class="text-xl font-semibold text-foreground">
          Add Document
        </h2>
        <button
          (click)="close()"
          class="p-2 rounded-lg hover:bg-muted transition-colors"
          [attr.aria-label]="'Close dialog'"
        >
          <svg
            class="w-5 h-5 text-muted-foreground"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <!-- Tab Navigation -->
      <div class="flex border-b border-border relative">
        <button
          (click)="activeTab.set('file')"
          class="flex-1 px-6 py-3 font-medium transition-all duration-300 relative"
          [class.text-primary-600]="activeTab() === 'file'"
          [class.bg-primary-50]="activeTab() === 'file'"
          [class.text-muted-foreground]="activeTab() !== 'file'"
          [class.hover:text-foreground]="activeTab() !== 'file'"
          [ngClass]="{
            'dark:bg-primary-900/20 hover:bg-muted/50': activeTab() === 'file'
          }"
        >
          <span class="relative z-10">Upload File</span>
        </button>
        <button
          (click)="activeTab.set('text')"
          class="flex-1 px-6 py-3 font-medium transition-all duration-300 relative"
          [class.text-primary-600]="activeTab() === 'text'"
          [class.bg-primary-50]="activeTab() === 'text'"
          [class.text-muted-foreground]="activeTab() !== 'text'"
          [class.hover:text-foreground]="activeTab() !== 'text'"
          [ngClass]="{
            'dark:bg-primary-900/20 hover:bg-muted/50': activeTab() === 'text'
          }"
        >
          <span class="relative z-10">Create Text</span>
        </button>
        <!-- Sliding indicator -->
        <div
          class="absolute bottom-0 h-0.5 bg-gradient-to-r from-primary-600 to-accent-600 transition-all duration-300"
          [style.width.%]="50"
          [style.left.%]="activeTab() === 'file' ? 0 : 50"
        ></div>
      </div>

      <!-- Content -->
      <div class="relative flex-1 flex flex-col">
        <!-- File Upload Tab -->
        @if (activeTab() === 'file') {
        <div class="flex-1 flex flex-col tab-content p-6">
          <div class="flex-1 flex flex-col space-y-4">
            <div
              class="flex-1 border-2 border-dashed border-border rounded-xl p-8 text-center transition-colors flex flex-col items-center justify-center"
              [class.border-primary-500]="isDragging()"
              [class.bg-primary-50]="isDragging()"
              [class.dark:bg-primary-900]="isDragging()"
              (dragover)="onDragOver($event)"
              (dragleave)="onDragLeave($event)"
              (drop)="onDrop($event)"
            >
              <input
                #fileInput
                type="file"
                accept=".pdf"
                (change)="onFileSelected($event)"
                class="hidden"
              />
              <svg
                class="w-12 h-12 mx-auto mb-4 text-muted-foreground"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              <p class="text-muted-foreground mb-2">
                Drag and drop your PDF here, or
              </p>
              <button
                (click)="fileInput.click()"
                class="text-primary-600 hover:text-primary-700 font-medium"
              >
                browse files
              </button>
              <p class="text-sm text-muted-foreground mt-2">
                Maximum file size: 10MB
              </p>
            </div>
            <!-- Selected File -->
            @if (selectedFile()) {
            <div
              class="flex items-center justify-between p-4 bg-muted rounded-lg"
            >
              <div class="flex items-center space-x-3">
                <svg
                  class="w-8 h-8 text-red-500"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-5L9 2H4z"
                    clip-rule="evenodd"
                  />
                </svg>
                <div>
                  <p class="font-medium text-foreground">
                    {{ selectedFile()!.name }}
                  </p>
                  <p class="text-sm text-muted-foreground">
                    {{ formatFileSize(selectedFile()!.size) }}
                  </p>
                </div>
              </div>
              <button
                (click)="clearSelectedFile()"
                class="p-2 rounded-lg hover:bg-muted transition-colors"
              >
                <svg
                  class="w-5 h-5 text-muted-foreground"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
            }
          </div>
        </div>
        }

        <!-- Text Upload Tab -->
        @if (activeTab() === 'text') {
        <div class="flex-1 flex flex-col tab-content p-6">
          <div class="flex-1 flex flex-col space-y-4">
            <div>
              <label
                for="document-title"
                class="block text-sm font-medium text-foreground mb-2"
              >
                Title
              </label>
              <input
                id="document-title"
                [(ngModel)]="textDocument.title"
                type="text"
                placeholder="Enter document title"
                class="w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors"
              />
            </div>
            <div class="flex-1 flex flex-col">
              <label
                for="document-content"
                class="block text-sm font-medium text-foreground mb-2"
              >
                Content
              </label>
              <textarea
                id="document-content"
                [(ngModel)]="textDocument.content"
                placeholder="Paste or type your content here..."
                class="flex-1 w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors resize-none"
              ></textarea>
              <p class="text-sm text-muted-foreground mt-1">
                {{ textDocument.content.length }} characters
              </p>
            </div>
          </div>
        </div>
        }
      </div>

      <!-- Upload Progress and Error Section -->
      <div class="px-6 pb-4">
        @if (isUploading()) {
        <div>
          <div class="flex items-center justify-between mb-2">
            <p class="text-sm font-medium text-foreground">
              {{ currentFileName() || 'Processing...' }}
            </p>
            <p class="text-sm text-muted-foreground">
              {{ getProgressText() }}
            </p>
          </div>
          <div class="w-full bg-muted rounded-full h-2 overflow-hidden">
            <div
              class="bg-gradient-to-r from-primary-500 to-accent-500 h-full transition-all duration-300"
              [style.width.%]="uploadProgress()"
            ></div>
          </div>
        </div>
        } @if (error() && !isUploading()) {
        <div
          class="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
        >
          <p class="text-sm text-red-600 dark:text-red-400">
            {{ error() }}
          </p>
        </div>
        }
      </div>

      <!-- Footer -->
      <div class="flex justify-end gap-3 p-6 border-t border-border">
        <button
          (click)="close()"
          class="px-4 py-2 text-muted-foreground hover:text-foreground transition-colors"
        >
          Cancel
        </button>
        <button
          (click)="handleUpload()"
          [disabled]="!canUpload() || isUploading()"
          class="px-6 py-2 bg-gradient-to-r from-primary-600 to-accent-600 text-white rounded-lg font-medium hover:shadow-lg transform hover:scale-[1.02] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
        >
          @if (!isUploading()) {
          <span>
            {{ activeTab() === 'file' ? 'Upload' : 'Create' }}
          </span>
          } @if (isUploading()) {
          <span class="flex items-center">
            <svg
              class="animate-spin -ml-1 mr-2 h-4 w-4"
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
            Processing...
          </span>
          }
        </button>
      </div>
    </div>
  `,
  styles: [
    `
      @keyframes scale-in {
        from {
          opacity: 0;
          transform: scale(0.95);
        }
        to {
          opacity: 1;
          transform: scale(1);
        }
      }

      .animate-scale-in {
        animation: scale-in 0.2s ease-out;
      }

      /* Tab content animation */
      @keyframes fadeInUp {
        from {
          opacity: 0;
          transform: translateY(10px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      .tab-content {
        animation: fadeInUp 0.3s ease-out;
      }

      /* Tab indicator animation */
      .tab-indicator {
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      }
    `,
  ],
})
export class UploadDialogComponent {
  private store = inject(Store);
  private modalRef = inject<ModalRef>(MODAL_REF);

  activeTab = signal<'file' | 'text'>('file');
  selectedFile = signal<File | null>(null);
  isDragging = signal(false);

  textDocument = {
    title: '',
    content: '',
  };

  // Store selectors as signals
  isUploading = this.store.selectSignal(uploadFeature.selectIsUploading);
  uploadProgress = this.store.selectSignal(uploadFeature.selectUploadProgress);
  currentFileName = this.store.selectSignal(
    uploadFeature.selectCurrentFileName
  );
  error = this.store.selectSignal(uploadFeature.selectUploadError);

  canUpload(): boolean {
    if (this.activeTab() === 'file') {
      return this.selectedFile() !== null;
    } else {
      return (
        this.textDocument.title.trim() !== '' &&
        this.textDocument.content.trim() !== ''
      );
    }
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging.set(true);
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging.set(false);
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging.set(false);

    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type === 'application/pdf') {
        this.selectedFile.set(file);
      }
    }
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.selectedFile.set(input.files[0]);
    }
  }

  clearSelectedFile(): void {
    this.selectedFile.set(null);
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  }

  async handleUpload(): Promise<void> {
    if (this.activeTab() === 'file' && this.selectedFile()) {
      const file = this.selectedFile();
      if (file) {
        this.store.dispatch(
          UploadActions.uploadFileCommand({
            file,
          })
        );
      }
    } else if (this.activeTab() === 'text') {
      this.store.dispatch(
        UploadActions.createTextDocumentCommand({
          title: this.textDocument.title.trim(),
          content: this.textDocument.content.trim(),
        })
      );
    }
  }

  getProgressText(): string {
    if (this.uploadProgress() === 100) {
      return 'Processing...';
    }
    return `${this.uploadProgress()}%`;
  }

  close(): void {
    this.modalRef.dismiss(undefined, 'cancel');
  }
}
