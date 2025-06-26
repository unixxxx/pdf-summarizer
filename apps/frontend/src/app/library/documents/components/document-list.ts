import {
  Component,
  inject,
  ChangeDetectionStrategy,
  signal,
  HostListener,
} from '@angular/core';

import { FormsModule } from '@angular/forms';
import { DocumentSearch } from './document-search';
import { DocumentCard } from './document-card';
import { Store } from '@ngrx/store';
import { UploadActions } from '../../upload/store/upload.actions';
import { DocumentActions } from '../store/document.actions';
import { documentFeature } from '../store/document.feature';
import { DocumentListItem } from '../store/state/document';
import { FolderActions } from '../../folder/store/folder.actions';

@Component({
  selector: 'app-document-list',
  standalone: true,
  imports: [FormsModule, DocumentSearch, DocumentCard],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      class="h-full flex flex-col"
      [class.dragging]="draggedDocumentId() !== null"
    >
      <!-- Search Bar -->
      <app-document-search
        (uploadClick)="openUploadDialog()"
        (searchChange)="onSearchChange($event)"
      />

      <!-- Document Grid -->
      <div class="flex-1 overflow-y-auto">
        <div class="p-4 pb-20">
          @if (documentsLoading()) {
          <div class="flex items-center justify-center py-12">
            <div class="text-center">
              <div class="inline-flex items-center gap-2 text-muted-foreground">
                <svg
                  class="animate-spin h-5 w-5"
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
                Loading documents...
              </div>
            </div>
          </div>
          } @else if (documentsEmpty() && !searchQuery) {
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
            <h3 class="mt-2 text-sm font-medium text-foreground">
              No documents
            </h3>
            <p class="mt-1 text-sm text-muted-foreground">
              Get started by uploading a PDF or text document.
            </p>
          </div>
          } @else if (documentsEmpty() && searchQuery) {
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
            @for (item of documents(); track item.id) {
            <app-document-card
              [item]="item"
              [isDragging]="draggedDocumentId() === item.id"
              (view)="viewDocument($event)"
              (delete)="deleteDocument($event)"
              (export)="exportDocument($event)"
              (startDrag)="onDocumentDragStart(item)"
              (endDrag)="onDocumentDragEnd()"
            />
            }
          </div>
          } @if (documentsError()) {
          <div class="mt-4 p-4 bg-error/10 border border-error/20 rounded-lg">
            <p class="text-sm text-error">{{ documentsError() }}</p>
          </div>
          }
        </div>
      </div>
    </div>
  `,
})
export class DocumentList {
  private readonly store = inject(Store);

  // Store selectors
  protected documents = this.store.selectSignal(
    documentFeature.selectDocumentList
  );
  protected documentsLoading = this.store.selectSignal(
    documentFeature.selectDocumentsLoading
  );
  protected documentsError = this.store.selectSignal(
    documentFeature.selectDocumentsError
  );
  protected documentsEmpty = this.store.selectSignal(
    documentFeature.selectDocumentsEmpty
  );

  // Local search state
  protected searchQuery = '';
  private currentFolderId: string | undefined;

  // Drag state
  protected draggedDocumentId = signal<string | null>(null);

  onSearchChange(query: string) {
    this.searchQuery = query;
    DocumentActions.fetchDocumentsCommand({
      criteria: {
        search: this.searchQuery || undefined,
        folder_id: this.currentFolderId,
      },
    });
  }

  viewDocument(item: DocumentListItem) {
    console.log('View document:', item);
    // TODO: Navigate to document view
  }

  deleteDocument(item: DocumentListItem) {
    this.store.dispatch(
      DocumentActions.openDeleteDocumentModalCommand({ document: item })
    );
  }

  exportDocument(event: {
    item: DocumentListItem;
    format: 'pdf' | 'markdown' | 'text';
  }) {
    this.store.dispatch(
      DocumentActions.exportDocumentCommand({
        documentId: event.item.documentId,
        format: event.format,
        filename: event.item.filename.replace(/\.[^/.]+$/, ''),
      })
    );
  }

  openUploadDialog() {
    this.store.dispatch(UploadActions.openUploadDialogCommand());
  }

  onDocumentDragStart(item: DocumentListItem) {
    this.draggedDocumentId.set(item.id);
  }

  onDocumentDragEnd() {
    this.draggedDocumentId.set(null);
    this.store.dispatch(
      FolderActions.setDragOverFolderCommand({ folderId: undefined })
    );
  }

  // Global drag end handler to ensure cleanup
  @HostListener('document:dragend')
  onGlobalDragEnd() {
    this.draggedDocumentId.set(null);
    this.store.dispatch(
      FolderActions.setDragOverFolderCommand({ folderId: undefined })
    );
  }
}
