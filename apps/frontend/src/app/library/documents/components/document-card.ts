import {
  Component,
  ChangeDetectionStrategy,
  input,
  output,
  signal,
  inject,
  computed,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { LibraryItem, DocumentStatus } from '../document.model';
import { formatFileSize } from '../../../core/utils/file-size.formatter';
import { formatRelativeDate } from '../../../core/utils/date.formatter';
import { TagListComponent } from '../../tag/components/tag-list';
import { LibraryStore } from '../../library.store';

@Component({
  selector: 'app-document-card',
  standalone: true,
  imports: [CommonModule, TagListComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      class="bg-card border border-border rounded-lg p-4 hover:shadow-lg transition-shadow cursor-pointer group relative"
      draggable="true"
      tabindex="0"
      role="button"
      (dragstart)="onDragStart($event)"
      (click)="view.emit(item())"
      (keydown.enter)="view.emit(item())"
      (keydown.space)="view.emit(item())"
    >
      <!-- Document Header -->
      <div class="flex items-start justify-between mb-3">
        <div class="flex-1 min-w-0">
          <h3
            class="font-medium text-foreground truncate"
            [title]="item().filename"
          >
            {{ item().filename }}
          </h3>
          <p class="text-xs text-muted-foreground mt-1">
            {{ formatFileSize(item().fileSize) }} •
            {{ formatDate(item().createdAt) }}
          </p>
        </div>
        <div
          class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <!-- Export Menu -->
          <div class="relative">
            <button
              (click)="toggleExportMenu($event)"
              class="p-1 hover:bg-muted rounded"
              title="Export"
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
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                />
              </svg>
            </button>
            @if (showExportMenu()) {
            <div
              class="absolute right-0 mt-1 w-32 bg-card border border-border rounded-lg shadow-lg z-10"
            >
              <button
                (click)="exportAs('markdown', $event)"
                class="w-full px-3 py-2 text-sm text-left hover:bg-muted"
              >
                Markdown
              </button>
              <button
                (click)="exportAs('pdf', $event)"
                class="w-full px-3 py-2 text-sm text-left hover:bg-muted"
              >
                PDF
              </button>
              <button
                (click)="exportAs('text', $event)"
                class="w-full px-3 py-2 text-sm text-left hover:bg-muted"
              >
                Plain Text
              </button>
            </div>
            }
          </div>

          <!-- Delete Button -->
          <button
            (click)="onDelete($event)"
            class="p-1 hover:bg-error/20 hover:text-error rounded"
            title="Delete"
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
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
        </div>
      </div>

      <!-- Summary Preview -->
      <p class="text-sm text-muted-foreground line-clamp-3 mb-3">
        {{ item().summary.content }}
      </p>

      <!-- Tags -->
      @if (item().summary.tags && item().summary.tags.length > 0) {
      <app-tag-list
        [tags]="item().summary.tags"
        variant="default"
        [clickable]="false"
        gapSize="small"
      />
      }

      <!-- Metadata -->
      <div
        class="mt-3 pt-3 border-t border-border flex items-center justify-between text-xs text-muted-foreground"
      >
        <span>{{ item().summary.wordCount | number : '1.0-0' }} words</span>

        <!-- Processing status or time -->
        @if (isProcessing()) {
        <div class="flex items-center gap-2 group/status">
          <!-- Circular progress indicator -->
          <div class="relative w-4 h-4">
            <svg class="w-4 h-4 transform -rotate-90">
              <!-- Background circle -->
              <circle
                cx="8"
                cy="8"
                r="6"
                stroke="currentColor"
                stroke-width="2"
                fill="none"
                class="text-primary/20"
              />
              <!-- Progress circle -->
              <circle
                cx="8"
                cy="8"
                r="6"
                stroke="currentColor"
                stroke-width="2"
                fill="none"
                class="text-primary"
                [style.stroke-dasharray]="'37.7 37.7'"
                [style.stroke-dashoffset]="
                  37.7 - (37.7 * (processingInfo()?.progress || 0)) / 100
                "
                style="transition: stroke-dashoffset 0.3s ease"
              />
            </svg>
          </div>
          <span class="relative">
            Processing
            <!-- Tooltip on hover -->
            <div
              class="absolute bottom-6 right-0 bg-popover border border-border rounded-md p-2 shadow-lg opacity-0 group-hover/status:opacity-100 transition-opacity pointer-events-none z-20 min-w-[150px]"
            >
              <p class="text-xs font-medium text-foreground">
                {{ getProcessingStageText() }}
              </p>
              @if (processingInfo()?.progress) {
              <p class="text-xs text-muted-foreground mt-1">
                Progress: {{ processingInfo()!.progress }}%
              </p>
              }
            </div>
          </span>
        </div>
        } @else if (isFailed()) {
        <div class="flex items-center gap-1 text-error">
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
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span>Failed</span>
        </div>
        }
      </div>
    </div>
  `,
})
export class DocumentCardComponent {
  // Services
  private libraryStore = inject(LibraryStore);

  // Input signals
  item = input.required<LibraryItem>();

  // Output signals
  view = output<LibraryItem>();
  delete = output<LibraryItem>();
  export = output<{ item: LibraryItem; format: 'pdf' | 'markdown' | 'text' }>();
  startDrag = output<DragEvent>();

  // State
  showExportMenu = signal(false);

  // Processing state - check both library store and document status
  isProcessing = computed(() => {
    const item = this.item();
    // Check if document is being tracked in library store
    const isTrackedProcessing = this.libraryStore.isDocumentProcessing()(
      item.documentId
    );
    // Also check the document's own status
    return (
      isTrackedProcessing ||
      item.status === DocumentStatus.PROCESSING ||
      item.status === DocumentStatus.UPLOADING
    );
  });

  processingInfo = computed(() => {
    const progress = this.libraryStore.getDocumentProgress()(
      this.item().documentId
    );
    return progress || null;
  });

  // Check if document failed
  isFailed = computed(() => this.item().status === DocumentStatus.FAILED);

  // Formatters
  formatFileSize = formatFileSize;
  formatDate = formatRelativeDate;

  getProcessingStageText(): string {
    const info = this.processingInfo();
    const item = this.item();

    // If we have real-time progress info, use that
    if (info && info.stage) {
      switch (info.stage) {
        case 'downloading':
          return 'Preparing document...';
        case 'extracting_text':
          return 'Extracting text...';
        case 'generating_embeddings':
          return 'Generating embeddings...';
        case 'generating_summary':
          return 'Creating summary...';
        case 'assigning_tags':
          return 'Assigning tags...';
        case 'completed':
          return 'Processing complete!';
        default:
          return 'Processing...';
      }
    }

    // Fall back to status-based text
    switch (item.status) {
      case DocumentStatus.UPLOADING:
        // If we're showing in library, upload is done, so it's processing
        return 'Processing document...';
      case DocumentStatus.PROCESSING:
        return 'Processing document...';
      case DocumentStatus.PENDING:
        return 'Queued for processing...';
      default:
        return 'Processing...';
    }
  }

  onDragStart(event: DragEvent) {
    event.dataTransfer?.setData('documentId', this.item().documentId);
    this.startDrag.emit(event);
  }

  onDelete(event: Event) {
    event.stopPropagation();
    this.delete.emit(this.item());
  }

  toggleExportMenu(event: Event) {
    event.stopPropagation();
    this.showExportMenu.update((value) => !value);
  }

  exportAs(format: 'pdf' | 'markdown' | 'text', event: Event) {
    event.stopPropagation();
    this.showExportMenu.set(false);
    this.export.emit({ item: this.item(), format });
  }
}
