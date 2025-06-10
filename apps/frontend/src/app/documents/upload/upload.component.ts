import {
  Component,
  inject,
  signal,
  computed,
  ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { SummaryService } from '../../summary/summary.service';
import {
  SummaryOptions,
  SummaryStyle,
  Summary,
} from '../../summary/summary.model';
import { DocumentMetadata } from '../document.model';
import { formatFileSize } from '../../shared/utils/formatters/file-size.formatter';

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8 animate-fade-in">
      <div class="text-center mb-8">
        <h1 class="text-3xl sm:text-4xl font-bold text-foreground mb-4">
          Upload & Summarize PDF
        </h1>
        <p class="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto">
          Upload your PDF document and get an AI-powered summary in seconds.
          Perfect for research papers, reports, and lengthy documents.
        </p>
      </div>

      <!-- Upload Zone -->
      <div
        class="relative glass rounded-2xl p-8 sm:p-12 text-center hover:shadow-xl transition-all duration-300 mb-8"
        (drop)="onDrop($event)"
        (dragover)="onDragOver($event)"
        (dragleave)="onDragLeave($event)"
        [class.border-primary-500]="isDragging()"
        [class.bg-primary-50]="isDragging()"
        [class.dark:bg-primary-900]="isDragging()"
      >
        @if (!file() && !uploading()) {
        <div class="space-y-4 animate-slide-up">
          <div
            class="mx-auto w-20 h-20 rounded-full bg-gradient-to-br from-primary-100 to-accent-100 dark:from-primary-900/30 dark:to-accent-900/30 flex items-center justify-center"
          >
            <svg
              class="w-10 h-10 text-primary-600 dark:text-primary-400"
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
          <div>
            <label for="file-upload" class="cursor-pointer">
              <span
                class="text-primary-600 dark:text-primary-400 font-medium hover:text-primary-700 dark:hover:text-primary-300"
              >
                Click to upload
              </span>
              <span class="text-muted-foreground"> or drag and drop</span>
            </label>
            <input
              id="file-upload"
              type="file"
              class="sr-only"
              accept="application/pdf"
              (change)="onFileSelected($event)"
            />
          </div>
          <p class="text-sm text-muted-foreground">PDF files up to 10MB</p>
        </div>
        }

        <!-- File Preview -->
        @if (file() && !uploading()) {
        <div class="space-y-4 animate-scale-in">
          <div
            class="mx-auto w-20 h-20 rounded-full bg-gradient-to-br from-accent-100 to-primary-100 dark:from-accent-900/30 dark:to-primary-900/30 flex items-center justify-center"
          >
            <svg
              class="w-10 h-10 text-accent-600 dark:text-accent-400"
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
            <p class="text-lg font-medium text-foreground">
              {{ file()!.name }}
            </p>
            <p class="text-sm text-muted-foreground">
              {{ formattedFileSize() }}
            </p>
          </div>
          <div class="flex justify-center gap-3">
            <button
              (click)="removeFile()"
              class="px-4 py-2 bg-muted hover:bg-muted/80 text-foreground rounded-lg transition-colors"
            >
              Remove
            </button>
            <button
              (click)="uploadFile()"
              class="px-6 py-2 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-700 hover:to-accent-700 text-white font-medium rounded-lg shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all"
            >
              Summarize PDF
            </button>
          </div>
        </div>
        }

        <!-- Upload Progress -->
        @if (uploading()) {
        <div class="space-y-6 animate-fade-in">
          <div class="mx-auto w-20 h-20 relative">
            <svg class="w-20 h-20 transform -rotate-90">
              <circle
                cx="40"
                cy="40"
                r="36"
                stroke="currentColor"
                stroke-width="8"
                fill="none"
                class="text-muted"
              />
              <circle
                cx="40"
                cy="40"
                r="36"
                stroke="currentColor"
                stroke-width="8"
                fill="none"
                [style.stroke-dasharray]="circumference"
                [style.stroke-dashoffset]="strokeDashoffset()"
                class="text-primary-600 transition-all duration-500"
              />
            </svg>
            <div class="absolute inset-0 flex items-center justify-center">
              <span class="text-2xl font-bold text-foreground"
                >{{ progress() }}%</span
              >
            </div>
          </div>
          <p class="text-lg font-medium text-foreground">
            {{ uploadStatus() }}
          </p>
          <p class="text-sm text-muted-foreground">
            Please wait while we process your document...
          </p>
        </div>
        }
      </div>

      <!-- Summary Options -->
      @if (file() && !uploading() && !success()) {
      <div class="glass rounded-xl p-6 mb-8 animate-slide-up">
        <h3 class="text-lg font-semibold text-foreground mb-4">
          Summary Options
        </h3>
        <div class="grid gap-4">
          <div>
            <div class="block text-sm font-medium text-foreground mb-2">
              Summary Style
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
              @for (style of summaryStyles; track style.value) {
              <button
                (click)="selectedStyle.set(style.value)"
                [class.bg-primary-600]="selectedStyle() === style.value"
                [class.text-white]="selectedStyle() === style.value"
                [class.bg-muted]="selectedStyle() !== style.value"
                class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                {{ style.label }}
              </button>
              }
            </div>
          </div>
        </div>
      </div>
      }

      <!-- Success State -->
      @if (success() && summary()) {
      <div class="glass rounded-2xl p-8 text-center animate-scale-in">
        <div
          class="mx-auto w-20 h-20 rounded-full bg-gradient-to-br from-success-100 to-success-200 dark:from-success-900/30 dark:to-success-800/30 flex items-center justify-center mb-6"
        >
          <svg
            class="w-10 h-10 text-success-600 dark:text-success-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-foreground mb-2">
          Summary Generated Successfully!
        </h2>
        <p class="text-muted-foreground mb-6">
          Your PDF has been processed in
          {{ summary()!.processingTime.toFixed(1) }} seconds
        </p>
        <div class="flex flex-col sm:flex-row justify-center gap-3">
          <button
            (click)="viewSummary()"
            class="px-6 py-3 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-700 hover:to-accent-700 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all"
          >
            View Summary
          </button>
          <button
            (click)="uploadAnother()"
            class="px-6 py-3 bg-muted hover:bg-muted/80 text-foreground font-medium rounded-xl transition-colors"
          >
            Upload Another
          </button>
        </div>
      </div>
      }

      <!-- Error State -->
      @if (error()) {
      <div
        class="glass rounded-2xl p-8 text-center border border-error/20 animate-shake"
      >
        <div
          class="mx-auto w-20 h-20 rounded-full bg-error/10 flex items-center justify-center mb-6"
        >
          <svg
            class="w-10 h-10 text-error"
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
        </div>
        <h2 class="text-2xl font-bold text-foreground mb-2">Upload Failed</h2>
        <p class="text-muted-foreground mb-6 max-w-md mx-auto">
          {{ error() }}
        </p>
        <button
          (click)="resetUpload()"
          class="px-6 py-3 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-700 hover:to-accent-700 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all"
        >
          Try Again
        </button>
      </div>
      }
    </div>
  `,
  styles: [],
})
export class UploadComponent {
  private summaryService = inject(SummaryService);
  private router = inject(Router);

  // State
  file = signal<File | null>(null);
  uploading = signal(false);
  progress = signal(0);
  uploadStatus = signal('');
  success = signal(false);
  error = signal<string | null>(null);
  isDragging = signal(false);
  summary = signal<Summary | null>(null);
  selectedStyle = signal<SummaryStyle>(SummaryStyle.BALANCED);

  // Summary style options
  summaryStyles = [
    { value: SummaryStyle.CONCISE, label: 'Concise' },
    { value: SummaryStyle.BALANCED, label: 'Balanced' },
    { value: SummaryStyle.DETAILED, label: 'Detailed' },
    { value: SummaryStyle.BULLET_POINTS, label: 'Bullet Points' },
  ];

  // Constants
  circumference = 2 * Math.PI * 36;

  // Computed
  strokeDashoffset = computed(() => {
    return this.circumference - (this.progress() / 100) * this.circumference;
  });

  formattedFileSize = computed(() => {
    const file = this.file();
    return file ? formatFileSize(file.size) : '';
  });

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      this.handleFile(input.files[0]);
    }
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    this.isDragging.set(false);

    if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
      this.handleFile(event.dataTransfer.files[0]);
    }
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    this.isDragging.set(true);
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    this.isDragging.set(false);
  }

  private handleFile(file: File) {
    // Validate file
    const metadata = new DocumentMetadata(file.name, file.size, file.type);

    if (!metadata.isValid) {
      this.error.set(metadata.validationErrors.join('. '));
      return;
    }

    this.file.set(file);
    this.error.set(null);
  }

  removeFile() {
    this.file.set(null);
    this.error.set(null);
  }

  uploadFile() {
    const file = this.file();
    if (!file) return;

    this.uploading.set(true);
    this.progress.set(0);
    this.uploadStatus.set('Uploading file...');
    this.error.set(null);

    // Simulate progress
    const progressInterval = setInterval(() => {
      if (this.progress() < 90) {
        this.progress.update((p) => p + 10);

        if (this.progress() > 30) {
          this.uploadStatus.set('Processing document...');
        }
        if (this.progress() > 60) {
          this.uploadStatus.set('Generating summary...');
        }
      }
    }, 300);

    // Create summary options
    const options = new SummaryOptions(this.selectedStyle());

    // Upload and summarize
    this.summaryService.uploadAndSummarize(file, options).subscribe({
      next: (summary) => {
        clearInterval(progressInterval);
        this.progress.set(100);
        this.uploadStatus.set('Complete!');
        this.summary.set(summary);

        setTimeout(() => {
          this.uploading.set(false);
          this.success.set(true);
        }, 500);
      },
      error: (err) => {
        clearInterval(progressInterval);
        this.uploading.set(false);
        this.error.set(err.message || 'Failed to process document');
      },
    });
  }

  viewSummary() {
    this.router.navigate(['/app/library']);
  }

  uploadAnother() {
    this.resetUpload();
  }

  resetUpload() {
    this.file.set(null);
    this.uploading.set(false);
    this.progress.set(0);
    this.uploadStatus.set('');
    this.success.set(false);
    this.error.set(null);
    this.summary.set(null);
    this.selectedStyle.set(SummaryStyle.BALANCED);
  }
}
