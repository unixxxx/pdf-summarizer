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
        [variant]="'small'"
        [clickable]="false"
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
                class="text-primary"
                [style.stroke-dasharray]="'37.7 37.7'"
                [style.stroke-dashoffset]="37.7"
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
                {{ processingStageText() }}
              </p>
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

  // Processing stage text
  processingStageText = computed(() => {
    const item = this.item();

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
}
