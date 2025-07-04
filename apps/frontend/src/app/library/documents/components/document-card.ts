import {
  Component,
  ChangeDetectionStrategy,
  input,
  output,
  signal,
  computed,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { TagList } from '../../tag/components/tag-list';
import { DocumentListItem } from '../store/state/document';
import { DocumentStatus } from '../dtos/document-status';
import { FormatDatePipe } from '../../../core/pipes/formatDate';
import { FormatFileSizePipe } from '../../../core/pipes/formatFileSize';

@Component({
  selector: 'app-document-card',
  standalone: true,
  imports: [CommonModule, TagList, FormatDatePipe, FormatFileSizePipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      class="bg-card border border-border rounded-lg p-4 hover:shadow-lg transition-all duration-200 cursor-pointer group relative"
      [class.opacity-0]="isDragging()"
      draggable="true"
      tabindex="0"
      role="button"
      (dragstart)="onDragStart($event)"
      (dragend)="onDragEnd()"
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
            {{ item().fileSize | formatFileSize }} •
            {{ item().createdAt | formatDate }}
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
        {{ item().summary }}
      </p>

      <!-- Tags -->
      @if (item().tags && item().tags.length > 0) {
      <app-tag-list
        [tags]="item().tags"
        [gapSize]="'small'"
      />
      }

      <!-- Metadata -->
      <div
        class="mt-3 pt-3 border-t border-border flex items-center justify-between text-xs text-muted-foreground"
      >
        <span>{{ item().wordCount | number : '1.0-0' }} words</span>

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
                class="text-primary transition-all duration-300 ease-out"
                stroke-dasharray="37.7"
                [style.stroke-dashoffset]="strokeDashOffset()"
              />
            </svg>
          </div>
          <span class="relative">
            {{
              processingProgress() > 0
                ? processingProgress() + '%'
                : 'Processing'
            }}
            <!-- Tooltip on hover -->
            <div
              class="absolute bottom-6 right-0 bg-popover border border-border rounded-md p-2 shadow-lg opacity-0 group-hover/status:opacity-100 transition-opacity pointer-events-none z-20 min-w-[200px]"
            >
              <p class="text-xs font-medium text-foreground">
                {{ processingStageText() }}
              </p>
              @if (processingProgress() > 0) {
              <div class="mt-1">
                <div class="w-full bg-primary/20 rounded-full h-1">
                  <div
                    class="bg-primary h-1 rounded-full transition-all duration-300"
                    [style.width.%]="processingProgress()"
                  ></div>
                </div>
              </div>
              }
            </div>
          </span>
        </div>
        } @else if (isFailed()) {
        <div class="flex items-center gap-1 text-error group/status">
          <button
            (click)="onRetry($event)"
            class="flex items-center gap-1 hover:underline"
            title="Retry processing"
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
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            <span class="relative">
              Retry
              <!-- Error tooltip on hover -->
              @if (item().errorMessage) {
              <div
                class="absolute bottom-6 right-0 bg-popover border border-border rounded-md p-2 shadow-lg opacity-0 group-hover/status:opacity-100 transition-opacity pointer-events-none z-20 min-w-[200px] max-w-[300px]"
              >
                <p class="text-xs font-medium text-error">
                  {{ item().errorMessage }}
                </p>
              </div>
              }
            </span>
          </button>
        </div>
        }
      </div>
    </div>
  `,
})
export class DocumentCard {
  // Input signals
  item = input.required<DocumentListItem>();
  isDragging = input<boolean>(false);

  // Output signals
  view = output<DocumentListItem>();
  delete = output<DocumentListItem>();
  export = output<{
    item: DocumentListItem;
    format: 'pdf' | 'markdown' | 'text';
  }>();
  retry = output<DocumentListItem>();
  startDrag = output<DocumentListItem>();
  endDrag = output<void>();

  // State
  showExportMenu = signal(false);

  // Processing state
  isProcessing = computed(() => {
    const item = this.item();
    return (
      item.status === DocumentStatus.PROCESSING ||
      item.status === DocumentStatus.UPLOADING ||
      item.status === DocumentStatus.PENDING
    );
  });

  // Check if document failed
  isFailed = computed(() => this.item().status === DocumentStatus.FAILED);

  // Processing progress (0-100)
  processingProgress = computed(() => {
    const item = this.item();
    return item.processingProgress || 0;
  });

  // Calculate stroke dash offset for circular progress
  strokeDashOffset = computed(() => {
    // Circumference of circle with radius 6 is ~37.7
    const circumference = 37.7;
    const progress = this.processingProgress() / 100;
    return circumference - circumference * progress;
  });

  // Processing stage text
  processingStageText = computed(() => {
    const item = this.item();
    const progress = this.processingProgress();

    // Simplified messages based on progress ranges
    if (progress === 0) {
      return 'Starting document processing...';
    } else if (progress < 15) {
      return 'Reading document...';
    } else if (progress < 30) {
      return 'Extracting text content...';
    } else if (progress < 40) {
      return 'Preparing for analysis...';
    } else if (progress < 65) {
      return 'Generating embeddings...';
    } else if (progress < 75) {
      return 'Preparing analysis...';
    } else if (progress < 90) {
      return 'Generating summary and tags...';
    } else if (progress < 100) {
      return 'Finalizing processing...';
    }

    // Fallback to status-based messages
    switch (item.status) {
      case DocumentStatus.UPLOADING:
        return 'Uploading document...';
      case DocumentStatus.PROCESSING:
        return 'Processing document...';
      case DocumentStatus.PENDING:
        return 'Queued for processing...';
      default:
        return 'Processing...';
    }
  });

  onDragStart(event: DragEvent) {
    if (event.dataTransfer) {
      event.dataTransfer.setData('text/plain', this.item().documentId);
      event.dataTransfer.setData('documentId', this.item().documentId);
      event.dataTransfer.setData('folderId', this.item().folderId ?? '');
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.dropEffect = 'move';
    }
    this.startDrag.emit(this.item());
  }

  onDragEnd() {
    this.endDrag.emit();
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

  onRetry(event: Event) {
    event.stopPropagation();
    this.retry.emit(this.item());
  }
}
