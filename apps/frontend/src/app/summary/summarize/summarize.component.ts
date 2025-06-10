import { Component, inject, computed, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { SummaryStore } from '../summary.store';
import { SummaryStyle } from '../summary.model';
import { formatFileSize } from '../../shared/utils/formatters/file-size.formatter';

@Component({
  selector: 'app-summarize',
  standalone: true,
  imports: [CommonModule, FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8 animate-fade-in">
      <div class="text-center mb-8">
        <h1 class="text-3xl sm:text-4xl font-bold text-foreground mb-4">
          AI Document Summarizer
        </h1>
        <p class="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto">
          Upload a PDF or paste text to get an intelligent summary. Customize
          the output with advanced options.
        </p>
      </div>

      <!-- Input Mode Selector -->
      <div class="flex justify-center mb-8">
        <div class="inline-flex rounded-xl bg-muted p-1">
          <button
            (click)="summaryStore.setInputMode('text')"
            [class.bg-background]="inputMode() === 'text'"
            [class.text-foreground]="inputMode() === 'text'"
            [class.shadow-sm]="inputMode() === 'text'"
            [class.text-muted-foreground]="inputMode() !== 'text'"
            class="px-6 py-2 rounded-lg font-medium transition-all"
          >
            <svg
              class="w-5 h-5 inline mr-2"
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
            Text Input
          </button>
          <button
            (click)="summaryStore.setInputMode('file')"
            [class.bg-background]="inputMode() === 'file'"
            [class.text-foreground]="inputMode() === 'file'"
            [class.shadow-sm]="inputMode() === 'file'"
            [class.text-muted-foreground]="inputMode() !== 'file'"
            class="px-6 py-2 rounded-lg font-medium transition-all"
          >
            <svg
              class="w-5 h-5 inline mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
              />
            </svg>
            PDF Upload
          </button>
        </div>
      </div>

      @if (!processing() && !success()) {
      <div class="grid lg:grid-cols-3 gap-6">
        <!-- Input Section -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Text Input -->
          @if (inputMode() === 'text') {
          <div class="glass rounded-2xl p-6">
            <label
              for="text-input"
              class="block text-sm font-medium text-foreground mb-2"
            >
              Enter your text
            </label>
            <textarea
              id="text-input"
              [ngModel]="inputText()"
              (ngModelChange)="summaryStore.setInputText($event)"
              placeholder="Paste or type your text here..."
              rows="12"
              class="w-full px-4 py-3 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              [class.border-error]="showError() && inputMode() === 'text'"
            ></textarea>
            <div class="mt-2 flex justify-between items-center">
              <span class="text-sm text-muted-foreground">
                {{ wordCount() }} words
              </span>
              @if (showError() && inputMode() === 'text') {
              <span class="text-sm text-error">
                Please enter at least 50 words
              </span>
              }
            </div>
          </div>
          }

          <!-- File Upload -->
          @if (inputMode() === 'file') {
          <div
            class="glass rounded-2xl p-8 text-center hover:shadow-xl transition-all duration-300"
            (drop)="onDrop($event)"
            (dragover)="onDragOver($event)"
            (dragleave)="onDragLeave($event)"
            [class.border-primary-500]="isDragging()"
            [class.bg-primary-50]="isDragging()"
            [class.dark:bg-primary-900]="isDragging()"
          >
            @if (!file()) {
            <div class="space-y-4">
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
                  accept="application/pdf,text/plain"
                  (change)="onFileSelected($event)"
                />
              </div>
              <p class="text-sm text-muted-foreground">
                PDF or text files up to 50MB
              </p>
            </div>
            } @else {
            <div class="space-y-4">
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
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div>
                <p class="font-medium text-foreground">{{ file()!.name }}</p>
                <p class="text-sm text-muted-foreground">
                  {{ formattedFileSize() }}
                </p>
              </div>
              <button
                (click)="removeFile()"
                class="text-sm text-muted-foreground hover:text-foreground"
              >
                Remove file
              </button>
            </div>
            }
          </div>
          }

          <!-- Example Templates (for text mode) -->
          @if (inputMode() === 'text' && !inputText()) {
          <div class="glass rounded-xl p-4">
            <h3 class="text-sm font-medium text-foreground mb-3">
              Try an example:
            </h3>
            <div class="flex flex-wrap gap-2">
              @for (example of examples; track example.name) {
              <button
                (click)="useExample(example)"
                class="px-3 py-1.5 text-sm bg-muted hover:bg-muted/80 rounded-lg transition-colors"
              >
                {{ example.name }}
              </button>
              }
            </div>
          </div>
          }
        </div>

        <!-- Options Section -->
        <div class="space-y-6">
          <!-- Summary Options -->
          <div class="glass rounded-xl p-6">
            <h3 class="text-lg font-semibold text-foreground mb-4">
              Summary Options
            </h3>

            <!-- Style Selection -->
            <div class="mb-6">
              <div class="block text-sm font-medium text-foreground mb-2">
                Summary Style
              </div>
              <div class="grid grid-cols-2 gap-2">
                @for (style of summaryStyles; track style.value) {
                <button
                  (click)="summaryStore.setSelectedStyle(style.value)"
                  [class.bg-primary-600]="selectedStyle() === style.value"
                  [class.text-white]="selectedStyle() === style.value"
                  [class.bg-muted]="selectedStyle() !== style.value"
                  class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  {{ style.label }}
                </button>
                }
              </div>
              <p class="mt-2 text-xs text-muted-foreground">
                {{ getStyleDescription(selectedStyle()) }}
              </p>
            </div>

            <!-- Max Length -->
            <div class="mb-6">
              <label
                for="max-length"
                class="block text-sm font-medium text-foreground mb-2"
              >
                Maximum Length (words)
              </label>
              <input
                id="max-length"
                type="number"
                [ngModel]="maxLength()"
                (ngModelChange)="summaryStore.setMaxLength($event)"
                min="50"
                max="5000"
                step="50"
                placeholder="Auto"
                class="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              <p class="mt-1 text-xs text-muted-foreground">
                Leave empty for automatic length (50-5000 words)
              </p>
            </div>

            <!-- Focus Areas -->
            <div class="mb-6">
              <label
                for="focus-areas"
                class="block text-sm font-medium text-foreground mb-2"
              >
                Focus Areas
              </label>
              <textarea
                id="focus-areas"
                [ngModel]="focusAreas()"
                (ngModelChange)="summaryStore.setFocusAreas($event)"
                placeholder="e.g., key findings, methodology, conclusions"
                rows="3"
                maxlength="500"
                class="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              ></textarea>
              <p class="mt-1 text-xs text-muted-foreground">
                Specify areas to emphasize ({{ focusAreas().length }}/500 chars)
              </p>
            </div>

            <!-- Custom Prompt -->
            <div>
              <label
                for="custom-prompt"
                class="block text-sm font-medium text-foreground mb-2"
              >
                Custom Instructions
              </label>
              <textarea
                id="custom-prompt"
                [ngModel]="customPrompt()"
                (ngModelChange)="summaryStore.setCustomPrompt($event)"
                placeholder="e.g., Use simple language, include technical details"
                rows="3"
                maxlength="1000"
                class="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              ></textarea>
              <p class="mt-1 text-xs text-muted-foreground">
                Additional instructions ({{ customPrompt().length }}/1000 chars)
              </p>
            </div>
          </div>

          <!-- Action Button -->
          <button
            (click)="generateSummary()"
            [disabled]="!canSummarize()"
            class="w-full px-6 py-3 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-700 hover:to-accent-700 disabled:from-gray-400 disabled:to-gray-500 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transform hover:scale-[1.02] disabled:transform-none transition-all disabled:cursor-not-allowed"
          >
            <span class="flex items-center justify-center">
              <svg
                class="w-5 h-5 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
              Generate Summary
            </span>
          </button>
        </div>
      </div>
      }

      <!-- Processing State -->
      @if (processing()) {
      <div class="glass rounded-2xl p-12 text-center">
        <div class="mx-auto w-20 h-20 relative mb-6">
          <div
            class="absolute inset-0 rounded-full border-4 border-muted animate-pulse-soft"
          ></div>
          <div
            class="absolute inset-0 rounded-full border-4 border-primary-600 border-t-transparent animate-spin"
          ></div>
        </div>
        <h2 class="text-2xl font-bold text-foreground mb-2">
          {{ processingStatus() }}
        </h2>
        <p class="text-muted-foreground">This usually takes 5-15 seconds...</p>
        @if (progress() > 0) {
        <div class="mt-6 max-w-xs mx-auto">
          <div class="bg-muted rounded-full h-2 overflow-hidden">
            <div
              class="bg-gradient-to-r from-primary-600 to-accent-600 h-full transition-all duration-300"
              [style.width.%]="progress()"
            ></div>
          </div>
          <p class="mt-2 text-sm text-muted-foreground">
            {{ progress() }}% complete
          </p>
        </div>
        }
      </div>
      }

      <!-- Success State -->
      @if (success() && summary()) {
      <div class="space-y-6 animate-fade-in">
        <div class="glass rounded-2xl p-6 sm:p-8">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-2xl font-bold text-foreground">
              Summary Generated
            </h2>
            <div class="flex items-center gap-2 text-sm text-muted-foreground">
              <svg
                class="w-4 h-4 text-accent-600 dark:text-accent-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
              <span>{{ summary()!.processingTime.toFixed(1) }}s</span>
            </div>
          </div>

          <!-- Summary Content -->
          <div class="prose prose-gray dark:prose-invert max-w-none mb-6">
            <div class="text-foreground/90 leading-relaxed whitespace-pre-wrap">
              {{ summary()!.content }}
            </div>
          </div>

          <!-- Tags -->
          @if (summary()!.tags.length > 0) {
          <div class="mb-6">
            <div class="flex flex-wrap gap-2">
              @for (tag of summary()!.tags; track tag.id) {
              <span
                class="px-3 py-1 text-xs font-medium rounded-full"
                [style.background-color]="tag.color + '20'"
                [style.color]="tag.color"
              >
                {{ tag.name }}
              </span>
              }
            </div>
          </div>
          }

          <!-- Summary Stats -->
          <div
            class="flex flex-wrap gap-4 text-sm text-muted-foreground border-t border-border pt-4"
          >
            <div class="flex items-center gap-1">
              <svg
                class="w-4 h-4"
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
              <span>{{ summary()!.wordCount }} words</span>
            </div>
            @if (inputMode() === 'text') {
            <div class="flex items-center gap-1">
              <svg
                class="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                />
              </svg>
              <span>{{ compressionRatio() }}% reduction</span>
            </div>
            }
          </div>

          <!-- Actions -->
          <div class="flex flex-col sm:flex-row gap-3 mt-6">
            <button
              (click)="copyToClipboard()"
              class="flex-1 px-6 py-3 bg-muted hover:bg-muted/80 text-foreground font-medium rounded-xl transition-colors flex items-center justify-center"
            >
              @if (copied()) {
              <svg
                class="w-5 h-5 mr-2 text-success-600"
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
              Copied! } @else {
              <svg
                class="w-5 h-5 mr-2"
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
              Copy Summary }
            </button>
            <button
              (click)="viewInLibrary()"
              class="flex-1 px-6 py-3 bg-muted hover:bg-muted/80 text-foreground font-medium rounded-xl transition-colors"
            >
              View in Library
            </button>
            <button
              (click)="summarizeAnother()"
              class="flex-1 px-6 py-3 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-700 hover:to-accent-700 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all"
            >
              Summarize Another
            </button>
          </div>
        </div>
      </div>
      }

      <!-- Error State -->
      @if (error()) {
      <div class="glass rounded-2xl p-8 text-center border border-error/20">
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
        <h2 class="text-2xl font-bold text-foreground mb-2">
          Summarization Failed
        </h2>
        <p class="text-muted-foreground mb-6 max-w-md mx-auto">{{ error() }}</p>
        <button
          (click)="tryAgain()"
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
export class SummarizeComponent {
  readonly summaryStore = inject(SummaryStore);
  private readonly router = inject(Router);

  // Expose store selectors for template
  readonly inputMode = this.summaryStore.inputMode;
  readonly inputText = this.summaryStore.inputText;
  readonly file = this.summaryStore.selectedFile;
  readonly processing = this.summaryStore.isProcessing;
  readonly processingStatus = this.summaryStore.processingStatus;
  readonly progress = this.summaryStore.progress;
  readonly success = computed(() => !this.summaryStore.isProcessing() && this.summaryStore.summary() !== null);
  readonly error = this.summaryStore.error;
  readonly summary = this.summaryStore.summary;
  readonly copied = this.summaryStore.copied;
  readonly showError = this.summaryStore.showError;
  readonly isDragging = this.summaryStore.isDragging;

  // Summary options
  readonly selectedStyle = this.summaryStore.selectedStyle;
  readonly maxLength = this.summaryStore.maxLength;
  readonly focusAreas = this.summaryStore.focusAreas;
  readonly customPrompt = this.summaryStore.customPrompt;

  // Computed values
  readonly wordCount = this.summaryStore.wordCount;
  readonly canSummarize = this.summaryStore.canSummarize;
  readonly compressionRatio = this.summaryStore.compressionRatio;

  // Summary style options
  summaryStyles = [
    { value: SummaryStyle.CONCISE, label: 'Concise' },
    { value: SummaryStyle.BALANCED, label: 'Balanced' },
    { value: SummaryStyle.DETAILED, label: 'Detailed' },
    { value: SummaryStyle.BULLET_POINTS, label: 'Bullets' },
  ];

  // Example templates
  examples = [
    { name: 'Research Paper', text: this.getExampleText('research') },
    { name: 'News Article', text: this.getExampleText('news') },
    { name: 'Business Report', text: this.getExampleText('business') },
  ];

  formattedFileSize = computed(() => {
    const file = this.file();
    return file ? formatFileSize(file.size) : '';
  });

  getStyleDescription(style: SummaryStyle): string {
    switch (style) {
      case SummaryStyle.CONCISE:
        return 'Brief overview with key points only';
      case SummaryStyle.BALANCED:
        return 'Standard summary with main ideas';
      case SummaryStyle.DETAILED:
        return 'Comprehensive summary with details';
      case SummaryStyle.BULLET_POINTS:
        return 'Structured list of key points';
      default:
        return '';
    }
  }

  useExample(example: { name: string; text: string }) {
    this.summaryStore.setInputText(example.text);
    this.summaryStore.clearError();
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      this.summaryStore.setFile(input.files[0]);
    }
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    this.summaryStore.setDragging(false);

    if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
      this.summaryStore.setFile(event.dataTransfer.files[0]);
    }
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    this.summaryStore.setDragging(true);
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    this.summaryStore.setDragging(false);
  }

  removeFile() {
    this.summaryStore.setFile(null);
  }

  generateSummary() {
    if (this.inputMode() === 'text') {
      this.summaryStore.summarizeText(undefined);
    } else {
      this.summaryStore.summarizeFile(undefined);
    }
  }

  copyToClipboard() {
    this.summaryStore.copyToClipboard();
  }

  viewInLibrary() {
    this.router.navigate(['/app/library']);
  }

  summarizeAnother() {
    this.summaryStore.reset();
  }

  tryAgain() {
    this.summaryStore.clearError();
    this.generateSummary();
  }

  private getExampleText(type: string): string {
    // Return example texts based on type
    const examples: Record<string, string> = {
      research: `Artificial intelligence (AI) has emerged as one of the most transformative technologies of the 21st century, fundamentally reshaping how we approach complex problems across various domains. Machine learning, a subset of AI, enables computers to learn from data without being explicitly programmed, while deep learning uses neural networks with multiple layers to progressively extract higher-level features from raw input.

Recent advances in natural language processing have led to the development of large language models that can understand and generate human-like text with remarkable accuracy. These models, trained on vast amounts of text data, have demonstrated capabilities in tasks ranging from translation and summarization to creative writing and code generation.

The implications of AI extend far beyond technology companies. In healthcare, AI systems are being used to diagnose diseases, predict patient outcomes, and accelerate drug discovery. In finance, machine learning algorithms detect fraudulent transactions and optimize trading strategies. Transportation is being revolutionized by autonomous vehicles that use computer vision and sensor fusion to navigate complex environments.

However, the rapid advancement of AI also raises important ethical considerations. Issues such as bias in algorithms, privacy concerns, job displacement, and the need for explainable AI systems require careful attention from researchers, policymakers, and society at large. As we continue to integrate AI into critical systems, ensuring transparency, fairness, and accountability becomes paramount.`,

      news: `Tech Giants Report Mixed Earnings as AI Investments Surge

Major technology companies released their quarterly earnings reports this week, revealing a complex picture of massive artificial intelligence investments coupled with varying financial performance across different sectors of the industry.

Apple reported revenue of $89.5 billion, slightly below analyst expectations, as iPhone sales in China faced increased competition from local manufacturers. However, the company's services division showed strong growth, with subscription revenue reaching an all-time high. CEO Tim Cook emphasized the company's commitment to integrating AI features across its product lineup, announcing a $10 billion investment in AI research and development over the next two years.

Microsoft exceeded Wall Street expectations with cloud revenue growing 28% year-over-year, driven largely by demand for AI services through its Azure platform. The company's partnership with OpenAI continues to pay dividends, with enterprise customers rapidly adopting AI-powered tools for productivity and development.

Google's parent company Alphabet reported advertising revenue growth of 11%, a recovery from previous quarters but still below pre-pandemic growth rates. The company's AI initiatives, including the Bard chatbot and various machine learning tools, are beginning to generate meaningful revenue, though specific figures were not disclosed.`,

      business: `Q4 2023 Performance Summary

Executive Overview:
The fourth quarter of 2023 marked a significant milestone for our organization, with total revenue reaching $45.2 million, representing a 23% year-over-year increase. This growth was primarily driven by strong performance in our cloud services division and successful expansion into the Asian market.

Key Financial Highlights:
- Revenue: $45.2M (+23% YoY)
- Operating Income: $12.1M (+18% YoY)
- Net Profit Margin: 26.8% (up from 24.2% in Q4 2022)
- Customer Acquisition: 2,847 new enterprise clients
- Customer Retention Rate: 94.6%

Product Performance:
Our cloud infrastructure services continued to be the primary growth driver, contributing 62% of total revenue. The newly launched AI-powered analytics platform exceeded expectations, generating $3.2M in its first full quarter. Mobile application downloads increased by 45%, with monthly active users reaching 1.2 million.

Market Expansion:
The Asian market expansion strategy yielded impressive results, with regional revenue growing 156% quarter-over-quarter. We established new offices in Singapore and Tokyo, and formed strategic partnerships with local technology providers.`,
    };

    return examples[type] || '';
  }
}
