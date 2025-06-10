import { Component, inject, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

import { ConfirmationModalComponent } from '../../shared/confirmation-modal.component';
import { LibraryStore } from '../library.store';
import { LibraryItem } from '../library.model';
import { formatFileSize } from '../../shared/utils/formatters/file-size.formatter';
import { formatRelativeDate } from '../../shared/utils/formatters/date.formatter';

@Component({
  selector: 'app-library',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    ConfirmationModalComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      class="max-w-7xl mx-auto py-4 sm:py-8 px-4 sm:px-6 lg:px-8 animate-fade-in"
    >
      <!-- Header -->
      <div class="mb-6 sm:mb-8">
        <h2 class="text-2xl sm:text-3xl font-bold text-foreground">
          Document Library
        </h2>
        <p class="mt-1 text-sm sm:text-base text-muted-foreground">
          Search, filter, and manage your PDF summaries
        </p>
      </div>

      <!-- Search and Filters Bar -->
      <div class="mb-6 space-y-4">
        <!-- Search Input -->
        <div class="relative">
          <svg
            class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            [(ngModel)]="searchQuery"
            (ngModelChange)="onSearchChange()"
            placeholder="Search by filename or content..."
            class="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          @if (searchQuery) {
          <button
            (click)="clearSearch()"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
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
          }
        </div>

        <!-- Tag Filters -->
        @if (availableTags().length > 0) {
        <div class="flex flex-wrap gap-2">
          <span class="text-sm text-muted-foreground mr-2"
            >Filter by tags:</span
          >
          @for (tag of availableTags(); track tag.id) {
          <button
            (click)="toggleTag(tag.slug)"
            [class.bg-primary-600]="selectedTags().includes(tag.slug)"
            [class.text-white]="selectedTags().includes(tag.slug)"
            [class.bg-muted]="!selectedTags().includes(tag.slug)"
            [class.text-foreground]="!selectedTags().includes(tag.slug)"
            class="px-3 py-1 text-sm rounded-full transition-colors"
          >
            {{ tag.name }}
            @if (tag.documentCount) {
            <span class="ml-1 opacity-75">({{ tag.documentCount }})</span>
            }
          </button>
          } @if (selectedTags().length > 0) {
          <button
            (click)="clearTags()"
            class="px-3 py-1 text-sm bg-error/10 text-error rounded-full hover:bg-error/20 transition-colors"
          >
            Clear all
          </button>
          }
        </div>
        }
      </div>

      <!-- Loading State -->
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
      }

      <!-- Empty State -->
      @if (!loading() && filteredItems().length === 0) {
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
          @if (hasActiveFilters()) { No documents match your filters } @else {
          No documents yet }
        </h3>
        <p class="text-muted-foreground mb-6">
          @if (hasActiveFilters()) { Try adjusting your search or filters }
          @else { Your PDF summaries will appear here once generated }
        </p>
        @if (!hasActiveFilters()) {
        <a
          routerLink="/app/summarize"
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
          Create Your First Summary
        </a>
        }
      </div>
      }

      <!-- Document Grid -->
      <div class="grid gap-4 md:gap-6 relative">
        @for (item of filteredItems(); track item.id) {
        <div
          class="glass rounded-xl p-4 sm:p-6 hover:shadow-xl transition-all duration-300 hover:scale-[1.01] group animate-slide-up relative overflow-visible"
          [style.animation-delay.ms]="filteredItems().indexOf(item) * 50"
        >
          <div class="relative z-0">
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
                  <h3
                    class="text-base sm:text-lg font-semibold text-foreground break-words pr-8 sm:pr-2"
                  >
                    {{ item.filename }}
                  </h3>
                </div>

                <!-- Tags -->
                @if (item.summary.tags && item.summary.tags.length > 0) {
                <div class="flex flex-wrap gap-1.5 mb-3">
                  @for (tag of item.summary.tags; track tag.id) {
                  <span
                    [style.background-color]="tag.color || '#6B7280'"
                    class="px-2 py-0.5 text-xs text-white rounded-full opacity-90"
                  >
                    {{ tag.name }}
                  </span>
                  }
                </div>
                }

                <!-- Metadata -->
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
                    {{ item.summary.wordCount }} words
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
                  @if (item.summary.processingTime) {
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
                    {{ item.summary.processingTime }}s
                  </span>
                  }
                </div>

                <!-- Summary Preview -->
                <p
                  class="text-sm sm:text-base text-foreground/80 line-clamp-2 sm:line-clamp-3 leading-relaxed mb-3"
                >
                  {{ item.summary.getPreview(200) }}
                </p>

                <!-- Actions -->
                <div class="flex items-center justify-between gap-3 flex-wrap">
                  <div class="flex items-center gap-2">
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
                    <button
                      (click)="startChat(item.documentId, item.filename)"
                      class="text-xs sm:text-sm font-medium text-accent-600 dark:text-accent-400 hover:text-accent-700 dark:hover:text-accent-300 inline-flex items-center group/btn"
                    >
                      <svg
                        class="w-3 h-3 sm:w-4 sm:h-4 mr-1"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                        />
                      </svg>
                      Chat
                    </button>
                  </div>
                  <div class="flex items-center gap-1">
                    <!-- Export buttons -->
                    <button
                      (click)="exportSummary(item.id, 'markdown')"
                      class="p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded transition-colors"
                      title="Export as Markdown"
                    >
                      <i class="fab fa-markdown text-sm"></i>
                    </button>
                    <button
                      (click)="exportSummary(item.id, 'pdf')"
                      class="p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded transition-colors"
                      title="Export as PDF"
                    >
                      <i class="far fa-file-pdf text-sm"></i>
                    </button>
                    <button
                      (click)="exportSummary(item.id, 'text')"
                      class="p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded transition-colors"
                      title="Export as Text"
                    >
                      <i class="far fa-file-alt text-sm"></i>
                    </button>
                    <button
                      (click)="downloadOriginal(item.documentId)"
                      class="p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded transition-colors"
                      title="Download original PDF"
                    >
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
                          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"
                        />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
            <!-- Delete button -->
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

      <!-- Summary Modal -->
      @if (showModal() && selectedItem()) {
      <div
        class="fixed inset-0 z-50 overflow-y-auto"
        aria-labelledby="modal-title"
        role="dialog"
        aria-modal="true"
      >
        <div
          class="flex items-center justify-center min-h-screen p-4 text-center"
        >
          <button
            class="fixed inset-0 bg-background/80 backdrop-blur-sm transition-opacity animate-fade-in cursor-default"
            (click)="closeModal()"
            (keydown.escape)="closeModal()"
            aria-label="Close modal"
            tabindex="0"
          ></button>

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
                      {{ selectedItem()!.filename }}
                    </h3>
                    <div
                      class="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs sm:text-sm text-muted-foreground mt-1"
                    >
                      <span>{{
                        formatFileSize(selectedItem()!.fileSize)
                      }}</span>
                      <span class="hidden sm:inline text-border">•</span>
                      <span>{{ selectedItem()!.summary.wordCount }} words</span>
                      <span class="hidden sm:inline text-border">•</span>
                      <span>{{ formatDate(selectedItem()!.createdAt) }}</span>
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

              <!-- Tags in Modal -->
              @if (selectedItem()!.summary.tags &&
              selectedItem()!.summary.tags.length > 0) {
              <div class="flex flex-wrap gap-1.5 mb-4">
                @for (tag of selectedItem()!.summary.tags; track tag.id) {
                <span
                  [style.background-color]="tag.color || '#6B7280'"
                  class="px-2 py-0.5 text-xs text-white rounded-full opacity-90"
                >
                  {{ tag.name }}
                </span>
                }
              </div>
              }

              <div class="prose prose-gray dark:prose-invert max-w-none">
                <div
                  class="text-sm sm:text-base text-foreground/90 leading-relaxed whitespace-pre-wrap max-h-[60vh] overflow-y-auto"
                >
                  {{ selectedItem()!.summary.content }}
                </div>
              </div>

              @if (selectedItem()!.summary.processingTime) {
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
                    {{ selectedItem()!.summary.processingTime }} seconds</span
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
        title="Delete Document"
        message="Are you sure you want to delete this document? This will also delete all associated chat sessions. This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        (confirmed)="deleteSummary()"
        (cancelled)="cancelDelete()"
      />
    </div>
  `,
  styles: [],
})
export class LibraryComponent {
  // Dependencies - only inject stores
  private readonly libraryStore = inject(LibraryStore);

  // Expose store selectors for template
  readonly filteredItems = this.libraryStore.filteredItems;
  readonly loading = this.libraryStore.isLoading;
  readonly selectedItem = this.libraryStore.selectedItem;
  readonly showModal = this.libraryStore.showModal;
  readonly showDeleteConfirm = this.libraryStore.showDeleteModal;
  readonly selectedTags = this.libraryStore.selectedTags;
  readonly availableTags = this.libraryStore.tags;
  readonly hasActiveFilters = this.libraryStore.hasActiveFilters;
  readonly error = this.libraryStore.error;

  // Search query - create a local property for two-way binding
  searchQuery = '';

  // Public formatter functions for template
  formatFileSize = formatFileSize;
  formatDate = formatRelativeDate;

  constructor() {
    // Initialize search query from store
    this.searchQuery = this.libraryStore.searchQuery();
  }

  onSearchChange() {
    this.libraryStore.search(this.searchQuery);
  }

  clearSearch() {
    this.searchQuery = '';
    this.libraryStore.clearFilters();
  }

  toggleTag(tagSlug: string) {
    this.libraryStore.toggleTag(tagSlug);
  }

  clearTags() {
    this.libraryStore.clearFilters();
  }

  exportSummary(summaryId: string, format: 'markdown' | 'pdf' | 'text') {
    this.libraryStore.exportSummary({ summaryId, format });
  }

  downloadOriginal(documentId: string) {
    this.libraryStore.downloadDocument(documentId);
  }

  confirmDelete(id: string) {
    this.libraryStore.confirmDelete(id);
  }

  deleteSummary() {
    this.libraryStore.deleteDocument(undefined);
  }

  cancelDelete() {
    this.libraryStore.cancelDelete();
  }

  viewFullSummary(item: LibraryItem) {
    this.libraryStore.selectItem(item);
  }

  closeModal() {
    this.libraryStore.closeModal();
  }

  startChat(documentId: string, filename: string) {
    this.libraryStore.startChat({ documentId, filename });
  }
}
