import {
  Component,
  inject,
  ChangeDetectionStrategy,
  signal,
  OnInit,
  DestroyRef,
} from '@angular/core';

import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { DocumentSearchComponent } from './document-search.component';
import { DocumentCardComponent } from './document-card.component';
import { UploadDialogComponent } from '../../upload/components/upload-dialog.component';
import { LibraryStore } from '../../library.store';
import { LibraryItem } from '../document.model';
import { Store } from '@ngrx/store';

@Component({
  selector: 'app-document-list',
  standalone: true,
  imports: [
    FormsModule,
    DocumentSearchComponent,
    DocumentCardComponent,
    UploadDialogComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <!-- Search Bar -->
    <app-document-search (uploadClick)="showUploadDialog.set(true)" />

    <!-- Document Grid -->
    <div class="p-6">
      @if (libraryStore.documentsLoading()) {
      <div class="flex items-center justify-center py-12">
        <div class="text-center">
          <div class="inline-flex items-center gap-2 text-muted-foreground">
            <svg class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
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
            Loading documents...
          </div>
        </div>
      </div>
      } @else if (libraryStore.documentsIsEmpty() &&
      !libraryStore.documentsIsSearching()) {
      <div class="text-center py-12">
        <svg
          class="mx-auto h-12 w-12 text-muted-foreground"
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
        <h3 class="mt-2 text-sm font-medium text-foreground">No documents</h3>
        <p class="mt-1 text-sm text-muted-foreground">
          <!-- @if (libraryStore.selectedFolderId() === 'unfiled') { No unfiled
          documents. Great job organizing! } @else if
          (libraryStore.selectedFolderId()) { This folder is empty. Drag
          documents here to organize them. } @else { Get started by uploading a
          PDF document. } -->
        </p>
      </div>
      } @else if (libraryStore.documentsIsEmpty() &&
      libraryStore.documentsIsSearching()) {
      <div class="text-center py-12">
        <svg
          class="mx-auto h-12 w-12 text-muted-foreground"
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
        <h3 class="mt-2 text-sm font-medium text-foreground">
          No results found
        </h3>
        <p class="mt-1 text-sm text-muted-foreground">
          Try adjusting your search or filters
        </p>
      </div>
      } @else {
      <div
        class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
      >
        @for (item of libraryStore.documents(); track item.id) {
        <app-document-card
          [item]="item"
          (view)="viewDocument($event)"
          (delete)="deleteDocument($event)"
          (export)="exportDocument($event)"
          (startDrag)="onDragStart($event)"
        />
        }
      </div>
      } @if (libraryStore.documentsHasError()) {
      <div class="mt-4 p-4 bg-error/10 border border-error/20 rounded-lg">
        <p class="text-sm text-error">{{ libraryStore.documentsError() }}</p>
      </div>
      }
    </div>

    <!-- Upload Dialog -->
    @if (showUploadDialog()) {
    <app-upload-dialog
      (closeDialog)="showUploadDialog.set(false)"
      (uploaded)="onDocumentUploaded()"
    />
    }
  `,
})
export class DocumentListComponent implements OnInit {
  protected libraryStore = inject(LibraryStore);
  private readonly store = inject(Store);
  protected showUploadDialog = signal(false);
  private route = inject(ActivatedRoute);
  private destroyRef = inject(DestroyRef);

  constructor() {
    // Initialize library store
    this.libraryStore.initialize();
  }

  ngOnInit() {
    // Listen to query parameter changes
    this.route.queryParams
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((params) => {
        const folderId = params['folderId'] || null;
        // this.libraryStore.selectFolder(folderId);
      });
  }

  onDocumentUploaded() {
    // Refresh the document list with a small delay to ensure backend has updated status
    setTimeout(() => {
      this.libraryStore.loadDocuments();
    }, 500);
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  viewDocument(item: LibraryItem) {
    // Navigate to document view
    // TODO: Implement navigation to document view
  }

  deleteDocument(item: LibraryItem) {
    this.libraryStore.confirmDeleteDocument(item);
  }

  exportDocument(event: {
    item: LibraryItem;
    format: 'pdf' | 'markdown' | 'text';
  }) {
    this.libraryStore.exportSummary({
      summaryId: event.item.id,
      format: event.format,
    });
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  onDragStart(event: DragEvent) {
    // Handle drag start
    // TODO: Implement drag functionality
  }
}
