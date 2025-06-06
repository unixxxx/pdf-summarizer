import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { RouterModule } from '@angular/router';
import { ConfirmationModalComponent } from '../shared/confirmation-modal.component';

interface SummaryItem {
  id: string;
  fileName: string;
  fileSize: number;
  summary: string;
  createdAt: string;
  processingTime: number;
  wordCount: number;
}

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [CommonModule, RouterModule, ConfirmationModalComponent],
  template: `
    <div class="max-w-7xl mx-auto py-4 sm:py-8 px-4 sm:px-6 lg:px-8 animate-fade-in">
      <div class="mb-6 sm:mb-8">
        <h2 class="text-2xl sm:text-3xl font-bold text-foreground">Summary History</h2>
        <p class="mt-1 text-sm sm:text-base text-muted-foreground">
          View and manage your previously generated summaries
        </p>
      </div>

      @if (loading()) {
      <div class="flex justify-center py-12">
        <div class="relative">
          <div
            class="w-16 h-16 rounded-full border-4 border-muted animate-pulse-soft"
          ></div>
          <div
            class="absolute top-0 left-0 w-16 h-16 rounded-full border-4 border-primary-600 border-t-transparent animate-spin"
          ></div>
        </div>
      </div>
      } @if (!loading() && summaries().length === 0) {
      <div class="text-center py-16 glass rounded-2xl">
        <div
          class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-primary-100 to-accent-100 dark:from-primary-900/30 dark:to-accent-900/30 mb-4"
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
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
        <h3 class="text-xl font-semibold text-foreground mb-2">
          No summaries yet
        </h3>
        <p class="text-muted-foreground mb-6">
          Your PDF summaries will appear here once generated
        </p>
        <a
          routerLink="/app/upload"
          class="inline-flex items-center px-6 py-3 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-700 hover:to-accent-700 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all"
        >
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
              d="M12 4v16m8-8H4"
            />
          </svg>
          Upload Your First PDF
        </a>
      </div>
      }

      <div class="grid gap-4 md:gap-6">
        @for (item of summaries(); track item.id) {
        <div
          class="glass rounded-xl p-4 sm:p-6 hover:shadow-xl transition-all duration-300 hover:scale-[1.01] group animate-slide-up"
          [style.animation-delay.ms]="summaries().indexOf(item) * 50"
        >
          <div class="relative">
            <div class="flex items-start gap-3">
              <div class="flex-shrink-0">
                <div
                  class="w-10 h-10 sm:w-12 sm:h-12 rounded-lg bg-gradient-to-br from-primary-100 to-accent-100 dark:from-primary-900/30 dark:to-accent-900/30 flex items-center justify-center"
                >
                  <svg
                    class="w-5 h-5 sm:w-6 sm:h-6 text-primary-600 dark:text-primary-400"
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
              </div>
              <div class="flex-1 min-w-0">
                <div class="mb-2">
                  <h3 class="text-base sm:text-lg font-semibold text-foreground break-words pr-8 sm:pr-2">
                    {{ item.fileName }}
                  </h3>
                </div>
                <div
                  class="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs sm:text-sm text-muted-foreground mb-3"
                >
                <span class="inline-flex items-center">
                  <svg
                    class="w-4 h-4 mr-1 opacity-60"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                    />
                  </svg>
                  {{ formatFileSize(item.fileSize) }}
                </span>
                <span class="hidden sm:inline text-border">•</span>
                <span class="inline-flex items-center">
                  <svg
                    class="w-4 h-4 mr-1 opacity-60"
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
                  {{ item.wordCount }} words
                </span>
                <span class="hidden sm:inline text-border">•</span>
                <span class="inline-flex items-center">
                  <svg
                    class="w-4 h-4 mr-1 opacity-60"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  {{ formatDate(item.createdAt) }}
                </span>
                @if (item.processingTime) {
                <span class="hidden sm:inline text-border">•</span>
                <span
                  class="inline-flex items-center text-accent-600 dark:text-accent-400"
                >
                  <svg
                    class="w-4 h-4 mr-1"
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
                  {{ item.processingTime }}s
                </span>
                }
              </div>
                <p class="text-sm sm:text-base text-foreground/80 line-clamp-2 sm:line-clamp-3 leading-relaxed mb-3">
                  {{ item.summary }}
                </p>
                <div class="flex items-center justify-between">
                  <button
                    (click)="viewFullSummary(item)"
                    class="text-xs sm:text-sm font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 inline-flex items-center group/btn"
                  >
                    Read more
                    <svg
                      class="w-3 h-3 sm:w-4 sm:h-4 ml-1 transform group-hover/btn:translate-x-1 transition-transform"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
            <!-- Mobile delete button -->
            <button
              (click)="confirmDelete(item.id)"
              class="absolute top-2 right-2 sm:opacity-0 sm:group-hover:opacity-100 p-2 text-muted-foreground hover:text-error hover:bg-error/10 rounded-lg transition-all"
              title="Delete summary"
            >
              <svg
                class="h-5 w-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          </div>
        </div>
        }
      </div>

      @if (showModal() && selectedSummary()) {
      <div
        class="fixed inset-0 z-50 overflow-y-auto"
        aria-labelledby="modal-title"
        role="dialog"
        aria-modal="true"
      >
        <div
          class="flex items-center justify-center min-h-screen p-4 text-center"
        >
          <div
            class="fixed inset-0 bg-background/80 backdrop-blur-sm transition-opacity animate-fade-in"
            (click)="closeModal()"
            (keydown.escape)="closeModal()"
            tabindex="0"
            role="button"
            aria-label="Close modal"
          ></div>

          <div
            class="relative inline-block align-bottom glass rounded-2xl text-left overflow-hidden shadow-2xl transform transition-all sm:my-8 sm:align-middle max-w-full sm:max-w-2xl w-full mx-4 sm:mx-0 animate-scale-in"
          >
            <div class="p-4 sm:p-6 lg:p-8">
              <div class="flex items-start justify-between mb-6">
                <div class="flex items-center gap-3">
                  <div
                    class="w-12 h-12 rounded-lg bg-gradient-to-br from-primary-100 to-accent-100 dark:from-primary-900/30 dark:to-accent-900/30 flex items-center justify-center"
                  >
                    <svg
                      class="w-6 h-6 text-primary-600 dark:text-primary-400"
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
                  <div class="flex-1 min-w-0">
                    <h3
                      class="text-lg sm:text-xl font-semibold text-foreground break-words"
                      id="modal-title"
                    >
                      {{ selectedSummary()!.fileName }}
                    </h3>
                    <div
                      class="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs sm:text-sm text-muted-foreground mt-1"
                    >
                      <span>{{
                        formatFileSize(selectedSummary()!.fileSize)
                      }}</span>
                      <span class="hidden sm:inline text-border">•</span>
                      <span>{{ selectedSummary()!.wordCount }} words</span>
                      <span class="hidden sm:inline text-border">•</span>
                      <span>{{
                        formatDate(selectedSummary()!.createdAt)
                      }}</span>
                    </div>
                  </div>
                </div>
                <button
                  (click)="closeModal()"
                  class="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all"
                >
                  <svg
                    class="w-5 h-5"
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

              <div class="prose prose-gray dark:prose-invert max-w-none">
                <div
                  class="text-sm sm:text-base text-foreground/90 leading-relaxed whitespace-pre-wrap max-h-[60vh] overflow-y-auto"
                >
                  {{ selectedSummary()!.summary }}
                </div>
              </div>

              @if (selectedSummary()!.processingTime) {
              <div class="mt-6 pt-6 border-t border-border">
                <div
                  class="flex items-center gap-2 text-sm text-muted-foreground"
                >
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
                  <span
                    >Processed in
                    {{ selectedSummary()!.processingTime }} seconds</span
                  >
                </div>
              </div>
              }
            </div>
          </div>
        </div>
      </div>
      }

      <app-confirmation-modal
        [isOpen]="showDeleteConfirm()"
        title="Delete Summary"
        message="Are you sure you want to delete this summary? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        (confirmed)="deleteSummary()"
        (cancelled)="cancelDelete()"
      />
    </div>
  `,
  styles: [],
})
export class HistoryComponent implements OnInit {
  private http = inject(HttpClient);

  summaries = signal<SummaryItem[]>([]);
  loading = signal(true);
  selectedSummary = signal<SummaryItem | null>(null);
  showModal = signal(false);
  showDeleteConfirm = signal(false);
  deleteTargetId = signal<string | null>(null);

  ngOnInit() {
    this.loadHistory();
  }

  loadHistory() {
    this.loading.set(true);
    this.http.get<SummaryItem[]>('/api/v1/pdf/history').subscribe({
      next: (data) => {
        this.summaries.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
      },
    });
  }

  confirmDelete(id: string) {
    this.deleteTargetId.set(id);
    this.showDeleteConfirm.set(true);
  }

  deleteSummary() {
    const id = this.deleteTargetId();
    if (id) {
      this.http.delete(`/api/v1/pdf/history/${id}`).subscribe({
        next: () => {
          this.summaries.update((items) =>
            items.filter((item) => item.id !== id)
          );
          this.cancelDelete();
        },
      });
    }
  }

  cancelDelete() {
    this.showDeleteConfirm.set(false);
    this.deleteTargetId.set(null);
  }

  formatFileSize(bytes: number): string {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i];
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();

    // Reset time parts for accurate day comparison
    const dateStart = new Date(
      date.getFullYear(),
      date.getMonth(),
      date.getDate()
    );
    const nowStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    const diffTime = nowStart.getTime() - dateStart.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
    });
  }

  viewFullSummary(item: SummaryItem) {
    this.selectedSummary.set(item);
    this.showModal.set(true);
  }

  closeModal() {
    this.showModal.set(false);
    this.selectedSummary.set(null);
  }
}
