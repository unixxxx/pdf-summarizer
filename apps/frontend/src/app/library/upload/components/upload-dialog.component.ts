import {
  Component,
  EventEmitter,
  Output,
  inject,
  signal,
  effect,
} from '@angular/core';

import { FormsModule } from '@angular/forms';
import { UploadStore } from '../upload.store';
import { CreateTextDocumentRequest } from '../upload.model';
import { LibraryStore } from '../../library.store';

@Component({
  selector: 'app-upload-dialog',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div
      class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      (click)="onBackdropClick($event)"
      (keydown.escape)="closeDialog.emit()"
      tabindex="0"
      role="button"
      [attr.aria-label]="'Close dialog backdrop'"
    >
      <div
        class="bg-card border border-border rounded-xl shadow-2xl w-full max-w-2xl animate-scale-in"
        (click)="$event.stopPropagation()"
        (keydown)="$event.stopPropagation()"
        role="dialog"
        [attr.aria-modal]="true"
        [attr.aria-labelledby]="'dialog-title'"
      >
        <!-- Header -->
        <div
          class="flex items-center justify-between p-6 border-b border-border"
        >
          <h2 id="dialog-title" class="text-xl font-semibold text-foreground">
            Add Document
          </h2>
          <button
            (click)="closeDialog.emit()"
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
        <div class="flex border-b border-border">
          <button
            (click)="activeTab.set('file')"
            [class]="getTabClass('file')"
            class="flex-1 px-6 py-3 font-medium transition-colors relative"
          >
            <span class="relative z-10">Upload File</span>
            @if (activeTab() === 'file') {
            <div
              class="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600"
            ></div>
            }
          </button>
          <button
            (click)="activeTab.set('text')"
            [class]="getTabClass('text')"
            class="flex-1 px-6 py-3 font-medium transition-colors relative"
          >
            <span class="relative z-10">Create Text</span>
            @if (activeTab() === 'text') {
            <div
              class="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600"
            ></div>
            }
          </button>
        </div>

        <!-- Content -->
        <div class="p-6">
          <!-- File Upload Tab -->
          @if (activeTab() === 'file') {
          <div class="space-y-4">
            <div
              class="border-2 border-dashed border-border rounded-xl p-8 text-center transition-colors"
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
          }

          <!-- Text Upload Tab -->
          @if (activeTab() === 'text') {
          <div class="space-y-4">
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
            <div>
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
                rows="10"
                class="w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors resize-none"
              ></textarea>
              <p class="text-sm text-muted-foreground mt-1">
                {{ textDocument.content.length }} characters
              </p>
            </div>
          </div>
          }

          <!-- Upload Progress -->
          @if (uploadStore.isUploading()) {
          <div class="mt-4">
            <div class="flex items-center justify-between mb-2">
              <p class="text-sm font-medium text-foreground">
                {{ uploadStore.currentFileName() || 'Processing...' }}
              </p>
              <p class="text-sm text-muted-foreground">
                {{ getProgressText() }}
              </p>
            </div>
            <div class="w-full bg-muted rounded-full h-2 overflow-hidden">
              <div
                class="bg-gradient-to-r from-primary-500 to-accent-500 h-full transition-all duration-300"
                [style.width.%]="uploadStore.uploadProgress()"
              ></div>
            </div>
            <p class="text-xs text-muted-foreground mt-1 text-center">
              {{ getStageText() }}
            </p>
          </div>
          }

          <!-- Error Message -->
          @if (uploadStore.error()) {
          <div
            class="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
          >
            <p class="text-sm text-red-600 dark:text-red-400">
              {{ uploadStore.error() }}
            </p>
          </div>
          }
        </div>

        <!-- Footer -->
        <div class="flex justify-end gap-3 px-6 pb-6">
          <button
            (click)="closeDialog.emit()"
            class="px-4 py-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            Cancel
          </button>
          <button
            (click)="handleUpload()"
            [disabled]="!canUpload() || uploadStore.isUploading()"
            class="px-6 py-2 bg-gradient-to-r from-primary-600 to-accent-600 text-white rounded-lg font-medium hover:shadow-lg transform hover:scale-[1.02] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            @if (!uploadStore.isUploading()) {
            <span>
              {{ activeTab() === 'file' ? 'Upload' : 'Create' }}
            </span>
            } @if (uploadStore.isUploading()) {
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
    `,
  ],
})
export class UploadDialogComponent {
  @Output() closeDialog = new EventEmitter<void>();
  @Output() uploaded = new EventEmitter<void>();

  uploadStore = inject(UploadStore);
  libraryStore = inject(LibraryStore);

  activeTab = signal<'file' | 'text'>('file');
  selectedFile = signal<File | null>(null);
  isDragging = signal(false);

  textDocument = {
    title: '',
    content: '',
  };

  private uploadSuccessful = false;

  constructor() {
    // Watch for upload completion - close immediately when upload finishes
    effect(() => {
      const progress = this.uploadStore.uploadProgress();
      const error = this.uploadStore.error();

      // When upload completes (100%), close the dialog immediately
      // Don't wait for processing to start
      if (progress === 100 && !error && !this.uploadSuccessful) {
        this.uploadSuccessful = true;
        // Emit the uploaded event so the library refreshes
        this.uploaded.emit();
        // Close the dialog immediately
        this.closeDialog.emit();
        // Reset the upload store for next upload
        this.uploadStore.reset();
      }
    });
  }

  getTabClass(tab: 'file' | 'text'): string {
    return this.activeTab() === tab
      ? 'text-primary-600 bg-primary-50 dark:bg-primary-900/20'
      : 'text-muted-foreground hover:text-foreground';
  }

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

  onBackdropClick(event: MouseEvent): void {
    if ((event.target as HTMLElement).classList.contains('fixed')) {
      this.closeDialog.emit();
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
        // const folderId = this.libraryStore.selectedFolderId();
        // this.uploadStore.uploadFile({ file, folderId: folderId || undefined });
      }
    } else if (this.activeTab() === 'text') {
      // const folderId = this.libraryStore.selectedFolderId();
      const request: CreateTextDocumentRequest = {
        title: this.textDocument.title.trim(),
        content: this.textDocument.content.trim(),
        // folder_id: folderId || undefined,
      };

      this.uploadStore.createTextDocument(request);
    }
  }

  getProgressText(): string {
    const progress = this.uploadStore.uploadProgress();
    if (progress === 100) {
      return 'Processing...';
    }
    return `${progress}%`;
  }

  getStageText(): string {
    const stage = this.uploadStore.currentStage();
    const progress = this.uploadStore.uploadProgress();

    // Map stage names to user-friendly descriptions
    switch (stage) {
      case 'downloading':
        return 'Preparing document...';
      case 'extracting_text':
        return 'Extracting text from PDF...';
      case 'generating_embeddings':
        return 'Generating embeddings...';
      case 'generating_summary':
        return 'Creating summary...';
      case 'completed':
        return 'Processing complete!';
      case 'error':
        return 'Error processing document';
      default:
        // Fallback to progress-based text
        if (progress < 30) {
          return 'Uploading file...';
        } else if (progress < 100) {
          return 'Processing document...';
        } else {
          return 'Finalizing...';
        }
    }
  }
}
