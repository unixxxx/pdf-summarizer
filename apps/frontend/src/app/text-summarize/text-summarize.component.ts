import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

interface TextSummaryResponse {
  summary: string;
  original_length: number;
  summary_length: number;
  original_words: number;
  summary_words: number;
  compression_ratio: number;
}

@Component({
  selector: 'app-text-summarize',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8 animate-fade-in">
      <div class="glass rounded-2xl shadow-xl p-8">
        <div class="mb-6">
          <h2 class="text-2xl font-bold text-foreground">
            Text Summarization
          </h2>
          <p class="mt-1 text-sm text-muted-foreground">
            Paste or type text to generate an AI-powered summary
          </p>
        </div>

        <div class="space-y-6">
          <!-- Text Input Area -->
          <div>
            <label for="text-input" class="block text-sm font-medium text-foreground mb-2">
              Text to Summarize
            </label>
            <textarea
              id="text-input"
              [(ngModel)]="inputText"
              rows="8"
              placeholder="Paste your text here..."
              class="w-full px-4 py-3 text-sm border border-border rounded-lg bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              [disabled]="isProcessing()"
            ></textarea>
            <div class="mt-2 flex justify-between text-xs text-muted-foreground">
              <span>{{ wordCount() }} words</span>
              <span>{{ characterCount() }} characters</span>
            </div>
          </div>

          <!-- Summary Customization Options -->
          @if (inputText()) {
          <div class="space-y-4 p-4 bg-muted/30 rounded-xl">
            <div>
              <label for="summary-length" class="block text-sm font-medium text-foreground mb-2">
                Summary Length
              </label>
              <div class="flex items-center gap-4">
                <input
                  id="summary-length"
                  type="range"
                  [(ngModel)]="summaryLength"
                  min="50"
                  max="500"
                  step="25"
                  class="flex-1 h-2 bg-muted rounded-lg appearance-none cursor-pointer slider"
                />
                <div class="w-24 text-center">
                  <span class="text-sm font-semibold text-primary-600 dark:text-primary-400">
                    {{ summaryLength() }}
                  </span>
                  <span class="text-xs text-muted-foreground ml-1">words</span>
                </div>
              </div>
              <div class="flex justify-between mt-1">
                <span class="text-xs text-muted-foreground">Concise</span>
                <span class="text-xs text-muted-foreground">Detailed</span>
              </div>
            </div>
            
            <div>
              <div class="block text-sm font-medium text-foreground mb-2">
                Summary Format
              </div>
              <div class="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  (click)="summaryFormat.set('paragraph')"
                  [class.ring-2]="summaryFormat() === 'paragraph'"
                  [class.ring-primary-600]="summaryFormat() === 'paragraph'"
                  [class.bg-primary-50]="summaryFormat() === 'paragraph'"
                  [class.dark:bg-primary-950]="summaryFormat() === 'paragraph'"
                  class="px-3 py-2 text-sm font-medium rounded-lg border border-border hover:bg-muted/50 transition-all"
                >
                  Paragraph
                </button>
                <button
                  type="button"
                  (click)="summaryFormat.set('bullets')"
                  [class.ring-2]="summaryFormat() === 'bullets'"
                  [class.ring-primary-600]="summaryFormat() === 'bullets'"
                  [class.bg-primary-50]="summaryFormat() === 'bullets'"
                  [class.dark:bg-primary-950]="summaryFormat() === 'bullets'"
                  class="px-3 py-2 text-sm font-medium rounded-lg border border-border hover:bg-muted/50 transition-all"
                >
                  Bullets
                </button>
                <button
                  type="button"
                  (click)="summaryFormat.set('keypoints')"
                  [class.ring-2]="summaryFormat() === 'keypoints'"
                  [class.ring-primary-600]="summaryFormat() === 'keypoints'"
                  [class.bg-primary-50]="summaryFormat() === 'keypoints'"
                  [class.dark:bg-primary-950]="summaryFormat() === 'keypoints'"
                  class="px-3 py-2 text-sm font-medium rounded-lg border border-border hover:bg-muted/50 transition-all"
                >
                  Key Points
                </button>
              </div>
            </div>
            
            <div>
              <label for="instructions" class="block text-sm font-medium text-foreground mb-2">
                Additional Instructions
                <span class="text-xs text-muted-foreground ml-1">(optional)</span>
              </label>
              <textarea
                id="instructions"
                [(ngModel)]="customInstructions"
                rows="2"
                placeholder="e.g., Focus on main arguments, Include examples..."
                class="w-full px-3 py-2 text-sm border border-border rounded-lg bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              ></textarea>
            </div>
          </div>
          }

          <!-- Action Buttons -->
          <div class="flex gap-3">
            <button
              (click)="summarizeText()"
              [disabled]="!canSummarize()"
              class="flex-1 px-6 py-3 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-700 hover:to-accent-700 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              @if (isProcessing()) {
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
                Generating Summary...
              </span>
              } @else { Generate Summary }
            </button>
            <button
              (click)="clearAll()"
              [disabled]="!inputText() && !summary()"
              class="px-6 py-3 border border-border hover:bg-muted/50 text-foreground font-medium rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Clear
            </button>
          </div>

          <!-- Error Display -->
          @if (error()) {
          <div class="p-4 bg-error/10 border border-error/20 rounded-xl animate-slide-up">
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

          <!-- Summary Display -->
          @if (summary() && summaryStats()) {
          <div class="space-y-4 animate-slide-up">
            <div class="flex items-center justify-between">
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

            <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div class="p-3 bg-muted/30 rounded-lg">
                <div class="text-muted-foreground text-xs">Original</div>
                <div class="font-semibold text-foreground">{{ summaryStats()!.original_words }} words</div>
              </div>
              <div class="p-3 bg-muted/30 rounded-lg">
                <div class="text-muted-foreground text-xs">Summary</div>
                <div class="font-semibold text-foreground">{{ summaryStats()!.summary_words }} words</div>
              </div>
              <div class="p-3 bg-muted/30 rounded-lg">
                <div class="text-muted-foreground text-xs">Compression</div>
                <div class="font-semibold text-accent-600 dark:text-accent-400">{{ summaryStats()!.compression_ratio }}%</div>
              </div>
              <div class="p-3 bg-muted/30 rounded-lg">
                <div class="text-muted-foreground text-xs">Processing</div>
                <div class="font-semibold text-foreground">{{ processingTime() }}s</div>
              </div>
            </div>
          </div>
          }
        </div>
      </div>
    </div>
  `,
})
export class TextSummarizeComponent {
  private http = inject(HttpClient);

  // Form state
  inputText = signal('');
  summaryLength = signal(200);
  summaryFormat = signal<'paragraph' | 'bullets' | 'keypoints'>('paragraph');
  customInstructions = signal('');

  // UI state
  isProcessing = signal(false);
  error = signal('');
  copySuccess = signal(false);

  // Results
  summary = signal('');
  summaryStats = signal<Omit<TextSummaryResponse, 'summary'> | null>(null);
  processingTime = signal(0);

  // Computed values
  wordCount = () => this.inputText().trim().split(/\s+/).filter(word => word.length > 0).length;
  characterCount = () => this.inputText().length;
  canSummarize = () => this.wordCount() >= 10 && !this.isProcessing();

  summarizeText() {
    if (!this.canSummarize()) return;

    this.isProcessing.set(true);
    this.error.set('');
    const startTime = Date.now();

    const requestBody = {
      text: this.inputText().trim(),
      max_length: this.summaryLength(),
      format: this.summaryFormat(),
      instructions: this.customInstructions().trim() || undefined,
    };

    this.http
      .post<TextSummaryResponse>('/api/v1/summarize/text', requestBody)
      .subscribe({
        next: (response) => {
          this.summary.set(response.summary);
          this.summaryStats.set({
            original_length: response.original_length,
            summary_length: response.summary_length,
            original_words: response.original_words,
            summary_words: response.summary_words,
            compression_ratio: response.compression_ratio,
          });
          this.processingTime.set((Date.now() - startTime) / 1000);
          this.isProcessing.set(false);
        },
        error: (err) => {
          this.error.set(err.error?.detail || 'Failed to generate summary');
          this.isProcessing.set(false);
        },
      });
  }

  copySummary() {
    navigator.clipboard.writeText(this.summary());
    this.copySuccess.set(true);
    setTimeout(() => this.copySuccess.set(false), 2000);
  }

  clearAll() {
    this.inputText.set('');
    this.summary.set('');
    this.summaryStats.set(null);
    this.error.set('');
    this.processingTime.set(0);
    this.summaryLength.set(200);
    this.summaryFormat.set('paragraph');
    this.customInstructions.set('');
  }
}