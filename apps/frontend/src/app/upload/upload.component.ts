import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8 animate-fade-in">
      <div class="glass rounded-2xl shadow-xl p-8">
        <div class="mb-6">
          <h2 class="text-2xl font-bold text-foreground">
            Upload PDF Document
          </h2>
          <p class="mt-1 text-sm text-muted-foreground">
            Transform your PDF into an intelligent summary
          </p>
        </div>

        <div
          class="relative border-2 border-dashed border-border hover:border-primary-400 dark:hover:border-primary-600 rounded-xl p-8 text-center transition-all duration-300 group"
          [class.border-primary-500]="isDragOver()"
          [class.bg-primary-50]="isDragOver()"
          [class.dark:bg-primary-950]="isDragOver()"
          (dragover)="onDragOver($event)"
          (dragleave)="onDragLeave($event)"
          (drop)="onDrop($event)"
        >
          <input
            type="file"
            id="file-upload"
            class="hidden"
            accept=".pdf"
            (change)="onFileSelected($event)"
          />
          <label for="file-upload" class="cursor-pointer">
            <div
              class="mx-auto w-16 h-16 rounded-full bg-gradient-to-br from-primary-100 to-accent-100 dark:from-primary-900/30 dark:to-accent-900/30 flex items-center justify-center group-hover:scale-110 transition-transform"
            >
              <svg
                class="w-8 h-8 text-primary-600 dark:text-primary-400"
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
            </div>
            <p class="mt-4 text-base font-medium text-foreground">
              <span
                class="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
                >Click to upload</span
              >
              or drag and drop
            </p>
            <p class="mt-1 text-sm text-muted-foreground">
              PDF files up to 10MB
            </p>
          </label>
        </div>

        @if (selectedFile()) {
        <div
          class="mt-6 p-4 bg-muted/50 rounded-xl border border-border animate-slide-up"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div
                class="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center"
              >
                <svg
                  class="w-5 h-5 text-primary-600 dark:text-primary-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
              <div>
                <p class="text-sm font-medium text-foreground">
                  {{ selectedFile()!.name }}
                </p>
                <p class="text-xs text-muted-foreground">
                  {{ formatFileSize(selectedFile()!.size) }}
                </p>
              </div>
            </div>
            <button
              (click)="removeFile()"
              class="p-1.5 hover:bg-muted rounded-lg transition-colors"
            >
              <svg
                class="w-4 h-4 text-muted-foreground"
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
          <button
            (click)="uploadFile()"
            [disabled]="isUploading()"
            class="mt-4 w-full px-6 py-3 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-700 hover:to-accent-700 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            @if (isUploading()) {
            <span class="flex items-center justify-center">
              <svg
                class="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
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
              Processing your PDF...
            </span>
            } @else { Generate Summary }
          </button>
        </div>
        } @if (summary()) {
        <div class="mt-8 animate-slide-up">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-xl font-semibold text-foreground">AI Summary</h3>
            <button
              (click)="copySummary()"
              class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-primary-600 dark:text-primary-400 hover:bg-primary-100 dark:hover:bg-primary-900/30 rounded-lg transition-colors"
            >
              <svg
                class="w-4 h-4 mr-1.5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                />
              </svg>
              {{ copySuccess() ? 'Copied!' : 'Copy' }}
            </button>
          </div>
          <div class="p-6 bg-card rounded-xl border border-border shadow-sm">
            <p class="text-foreground whitespace-pre-wrap leading-relaxed">
              {{ summary() }}
            </p>
          </div>
        </div>
        } @if (error()) {
        <div
          class="mt-6 p-4 bg-error/10 border border-error/20 rounded-xl animate-slide-up"
        >
          <div class="flex">
            <svg
              class="w-5 h-5 text-error flex-shrink-0 mt-0.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p class="ml-3 text-sm text-error">{{ error() }}</p>
          </div>
        </div>
        }
      </div>
    </div>
  `,
})
export class UploadComponent {
  private http = inject(HttpClient);

  selectedFile = signal<File | null>(null);
  isUploading = signal(false);
  summary = signal<string>('');
  error = signal<string>('');
  isDragOver = signal(false);
  copySuccess = signal(false);

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      this.selectedFile.set(input.files[0]);
      this.summary.set('');
      this.error.set('');
    }
  }

  uploadFile() {
    const file = this.selectedFile();
    if (!file) return;

    this.isUploading.set(true);
    this.error.set('');

    const formData = new FormData();
    formData.append('file', file);

    this.http
      .post<{ summary: string }>('/api/v1/pdf/summarize', formData)
      .subscribe({
        next: (response) => {
          this.summary.set(response.summary);
          this.isUploading.set(false);
        },
        error: (err) => {
          this.error.set(err.error?.detail || 'Failed to process PDF');
          this.isUploading.set(false);
        },
      });
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver.set(true);
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver.set(false);
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver.set(false);

    const files = event.dataTransfer?.files;
    if (files && files.length > 0 && files[0].type === 'application/pdf') {
      this.selectedFile.set(files[0]);
      this.summary.set('');
      this.error.set('');
    }
  }

  removeFile() {
    this.selectedFile.set(null);
    this.summary.set('');
    this.error.set('');
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  copySummary() {
    navigator.clipboard.writeText(this.summary());
    this.copySuccess.set(true);
    setTimeout(() => this.copySuccess.set(false), 2000);
  }
}
