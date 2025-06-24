import { computed, inject } from '@angular/core';
import {
  patchState,
  signalStore,
  withComputed,
  withMethods,
  withState,
} from '@ngrx/signals';
import { rxMethod } from '@ngrx/signals/rxjs-interop';
import { tapResponse } from '@ngrx/operators';
import { pipe, switchMap, tap, of } from 'rxjs';

import {
  DocumentService,
  DocumentSearchCriteria,
} from './documents/document.service';
import { TagService } from './tag/services/tag.service';
import {
  WebSocketService,
  DocumentProcessingEvent,
} from '../core/services/websocket.service';
import { UIStore } from '../shared/ui.store';

import { LibraryItem } from './documents/document.model';
import { Tag } from './tag/store/state/tag';

type DialogData = LibraryItem;

// Simplified state structure with logical groupings
export interface LibraryState {
  // Core data
  documents: LibraryItem[];
  tags: Tag[];

  // Document processing tracking
  processingDocuments: Record<string, { stage: string; progress: number }>;

  // UI Navigation

  // Search & Filter
  searchQuery: string;

  // Metadata
  counts: {
    total: number;
    unfiled: number;
    documentsTotal: number;
  };

  // Pagination
  pagination: {
    limit: number;
    offset: number;
    hasMore: boolean;
  };

  // Loading states - unified
  loading: {
    folders: boolean;
    documents: boolean;
    documentsMore: boolean;
    tags: boolean;
  };

  // Error handling - unified
  errors: {
    documents: string | null;
  };

  // Dialog state - generic
  dialog: {
    type: 'folder' | 'deleteFolder' | 'deleteDocument' | null;
    data: DialogData | null;
  };

  // Drag state
  dragOverFolder: string | null;
}

const initialState: LibraryState = {
  documents: [],
  tags: [],
  processingDocuments: {},
  searchQuery: '',
  counts: {
    total: 0,
    unfiled: 0,
    documentsTotal: 0,
  },
  pagination: {
    limit: 50,
    offset: 0,
    hasMore: false,
  },
  loading: {
    folders: false,
    documents: false,
    documentsMore: false,
    tags: false,
  },
  errors: {
    documents: null,
  },
  dialog: {
    type: null,
    data: null,
  },
  dragOverFolder: null,
};

export const LibraryStore = signalStore(
  { providedIn: 'root' },
  withState(initialState),
  withComputed((store) => ({
    // Simplified computed properties
    isLoading: computed(() =>
      Object.values(store.loading()).some((loading) => loading)
    ),

    documentsIsEmpty: computed(() => store.documents().length === 0),
    documentsHasError: computed(() => store.errors().documents !== null),
    documentsIsSearching: computed(() => store.searchQuery().length > 0),

    tagsIsEmpty: computed(() => store.tags().length === 0),

    // Dialog helpers
    isDialogOpen: computed(() => store.dialog().type !== null),
    dialogType: computed(() => store.dialog().type),
    dialogData: computed(() => store.dialog().data),

    showDeleteDocumentConfirm: computed(
      () => store.dialog().type === 'deleteDocument'
    ),
    deletingDocument: computed(() =>
      store.dialog().type === 'deleteDocument'
        ? (store.dialog().data as LibraryItem)
        : null
    ),

    // Legacy computed properties for compatibility
    documentsLoading: computed(() => store.loading().documents),
    documentsLoadingMore: computed(() => store.loading().documentsMore),
    documentsError: computed(() => store.errors().documents),
    tagsLoading: computed(() => store.loading().tags),
    documentsTotal: computed(() => store.counts().documentsTotal),
    documentsLimit: computed(() => store.pagination().limit),
    documentsOffset: computed(() => store.pagination().offset),
    documentsHasMore: computed(() => store.pagination().hasMore),
    totalDocumentCount: computed(() => store.counts().total),
    unfiledCount: computed(() => store.counts().unfiled),

    // Document processing tracking
    processingDocumentIds: computed(() =>
      Object.keys(store.processingDocuments())
    ),
    processingDocumentsCount: computed(
      () => Object.keys(store.processingDocuments()).length
    ),
    isDocumentProcessing: computed(
      () => (documentId: string) => documentId in store.processingDocuments()
    ),
    getDocumentProgress: computed(
      () => (documentId: string) => store.processingDocuments()[documentId]
    ),

    // Constants
    availableColors: computed(() => [
      '#6B7280',
      '#EF4444',
      '#F59E0B',
      '#10B981',
      '#3B82F6',
      '#6366F1',
      '#8B5CF6',
      '#EC4899',
    ]),
  })),

  withMethods((store) => {
    const documentService = inject(DocumentService);
    const tagService = inject(TagService);
    const uiStore = inject(UIStore);
    const webSocketService = inject(WebSocketService);

    // Subscribe to WebSocket document processing updates
    webSocketService.documentProcessing$
      .pipe(
        tap((event: DocumentProcessingEvent) => {
          const processingDocs = { ...store.processingDocuments() };

          // Track all processing documents
          if (event.stage === 'completed' || event.progress >= 100) {
            delete processingDocs[event.document_id];
          } else if (event.stage === 'error') {
            delete processingDocs[event.document_id];
          } else {
            processingDocs[event.document_id] = {
              stage: event.stage,
              progress: event.progress,
            };
          }

          patchState(store, { processingDocuments: processingDocs });
        })
      )
      .subscribe();

    // Generic error handler
    const handleError = (message: string, error?: unknown) => {
      console.error(message, error);
      uiStore.showNotification(message, 'error');
    };

    // Generic success handler
    const handleSuccess = (message: string) => {
      uiStore.showNotification(message, 'success');
    };

    // Dialog management helpers
    const openDialog = (
      type: LibraryState['dialog']['type'],
      data: DialogData | null = null
    ) => {
      patchState(store, { dialog: { type, data } });
    };

    const closeDialog = () => {
      patchState(store, { dialog: { type: null, data: null } });
    };

    // Reusable delete method factory
    const createDeleteMethod = (
      serviceFn: (id: string) => import('rxjs').Observable<unknown>,
      successMessage: string,
      afterDelete?: () => void
    ) =>
      rxMethod<string>(
        switchMap((id) =>
          serviceFn(id).pipe(
            tapResponse({
              next: () => {
                handleSuccess(successMessage);
                closeDialog();
                afterDelete?.();
              },
              error: () =>
                handleError(`Failed to ${successMessage.toLowerCase()}`),
            })
          )
        )
      );

    // Loading state helpers
    const setLoading = (key: keyof LibraryState['loading'], value: boolean) => {
      patchState(store, {
        loading: { ...store.loading(), [key]: value },
      });
    };

    const loadDocuments = rxMethod<void>(
      pipe(
        tap(() => {
          setLoading('documents', true);
          patchState(store, {
            errors: { ...store.errors(), documents: null },
            pagination: { ...store.pagination(), offset: 0 },
          });
        }),
        switchMap(() => {
          const criteria: DocumentSearchCriteria = {
            searchQuery: store.searchQuery(),
            limit: store.pagination().limit,
            offset: 0,
          };
          return documentService.browse(criteria).pipe(
            tapResponse({
              next: (response) => {
                const items = response.items.map((dto) =>
                  LibraryItem.fromDto(dto)
                );
                patchState(store, {
                  documents: items,
                  loading: { ...store.loading(), documents: false },
                  counts: { ...store.counts(), documentsTotal: response.total },
                  pagination: {
                    ...store.pagination(),
                    offset: response.offset,
                    hasMore: response.has_more,
                  },
                });
              },
              error: (error: Error) =>
                patchState(store, {
                  errors: { ...store.errors(), documents: error.message },
                  loading: { ...store.loading(), documents: false },
                }),
            })
          );
        })
      )
    );

    // Document operations
    const deleteDocument = createDeleteMethod(
      (id) => documentService.delete(id),
      'Document deleted successfully',
      () => {
        const deletedDoc = store.dialog().data as LibraryItem;
        if (deletedDoc) {
          patchState(store, {
            documents: store
              .documents()
              .filter((d) => d.documentId !== deletedDoc.documentId),
            counts: {
              ...store.counts(),
              documentsTotal: store.counts().documentsTotal - 1,
            },
          });
        }
      }
    );

    return {
      // Initialization
      initialize(): void {
        loadDocuments(undefined);
        // Tags are loaded by NgRx store in app.routes.ts
      },

      // Data loading
      loadDocuments,
      // loadTags,

      // Search & Filter
      setSearchQuery(searchQuery: string): void {
        patchState(store, { searchQuery });
      },

      // Tag-related methods removed - tags are selected through UI only

      clearFilters(): void {
        patchState(store, {
          searchQuery: '',
        });
      },

      // Dialog management

      confirmDeleteDocument(document: LibraryItem): void {
        openDialog('deleteDocument', document);
      },

      cancelDeleteFolder(): void {
        closeDialog();
      },

      cancelDeleteDocument(): void {
        closeDialog();
      },

      executeDeleteDocument(): void {
        const document = store.dialog().data as LibraryItem;
        if (document?.documentId) {
          deleteDocument(document.documentId);
        }
      },

      // Drag & Drop
      setDragOverFolder(folderId: string | null): void {
        patchState(store, { dragOverFolder: folderId });
      },

      handleDrop(folderId: string, documentId: string): void {
        patchState(store, { dragOverFolder: null });
      },

      // Document operations
      loadMoreDocuments: rxMethod<void>(
        pipe(
          tap(() => {
            if (store.loading().documentsMore || !store.pagination().hasMore)
              return;
            setLoading('documentsMore', true);
          }),
          switchMap(() => {
            if (store.loading().documentsMore || !store.pagination().hasMore)
              return of(null);

            const newOffset =
              store.pagination().offset + store.pagination().limit;
            const criteria: DocumentSearchCriteria = {
              searchQuery: store.searchQuery(),
              folderId: undefined,
              unfiled: false,
              limit: store.pagination().limit,
              offset: newOffset,
            };
            return documentService.browse(criteria).pipe(
              tapResponse({
                next: (response) => {
                  if (response) {
                    const newItems = response.items.map((dto) =>
                      LibraryItem.fromDto(dto)
                    );
                    patchState(store, {
                      documents: [...store.documents(), ...newItems],
                      loading: { ...store.loading(), documentsMore: false },
                      pagination: {
                        ...store.pagination(),
                        offset: response.offset,
                        hasMore: response.has_more,
                      },
                    });
                  }
                },
                error: (error: Error) => {
                  patchState(store, {
                    errors: { ...store.errors(), documents: error.message },
                    loading: { ...store.loading(), documentsMore: false },
                  });
                },
              })
            );
          })
        )
      ),

      exportSummary: rxMethod<{
        summaryId: string;
        format: 'pdf' | 'markdown' | 'text';
      }>(
        switchMap(({ summaryId, format }) =>
          documentService.exportSummary(summaryId, format).pipe(
            tapResponse({
              next: (blob) => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `summary.${format}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
              },
              error: (error: Error) =>
                patchState(store, {
                  errors: { ...store.errors(), documents: error.message },
                }),
            })
          )
        )
      ),

      // Helper methods
      getTagById(tagId: string): Tag | undefined {
        return store.tags().find((tag) => tag.id === tagId);
      },

      getTagBySlug(slug: string): Tag | undefined {
        return store.tags().find((tag) => tag.slug === slug);
      },
    };
  })
);
