import { inject, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { LibraryService } from './library.service';
import { DocumentService } from './document.service';
import { SummaryService } from '../summary/summary.service';
import { ChatService } from '../chat/chat.service';
import { LibraryItem, Tag } from './library.model';
import { UIStore } from '../shared/ui.store';
import { debounceTime, distinctUntilChanged, switchMap, tap } from 'rxjs/operators';
import { Subject, of } from 'rxjs';
import { tapResponse } from '@ngrx/operators';
import {
  patchState,
  signalStore,
  withComputed,
  withMethods,
  withState,
  withHooks,
} from '@ngrx/signals';
import { rxMethod } from '@ngrx/signals/rxjs-interop';

interface LibraryState {
  items: LibraryItem[];
  tags: Tag[];
  selectedTags: string[];
  searchQuery: string;
  sortBy: 'date' | 'title' | 'size';
  sortOrder: 'asc' | 'desc';
  isLoading: boolean;
  error: string | null;
  // Modal states
  selectedItem: LibraryItem | null;
  showModal: boolean;
  showDeleteModal: boolean;
  deleteTargetId: string | null;
}

const initialState: LibraryState = {
  items: [],
  tags: [],
  selectedTags: [],
  searchQuery: '',
  sortBy: 'date',
  sortOrder: 'desc',
  isLoading: false,
  error: null,
  selectedItem: null,
  showModal: false,
  showDeleteModal: false,
  deleteTargetId: null,
};

export const LibraryStore = signalStore(
  { providedIn: 'root' },
  withState(initialState),
  withComputed((store) => ({
    // Since we're doing server-side filtering, just return the items as-is
    filteredItems: computed(() => store.items()),

    hasActiveFilters: computed(() => {
      return store.searchQuery().length > 0 || store.selectedTags().length > 0;
    }),
  })),
  withMethods((store) => {
    const libraryService = inject(LibraryService);
    const documentService = inject(DocumentService);
    const summaryService = inject(SummaryService);
    const chatService = inject(ChatService);
    const uiStore = inject(UIStore);
    const router = inject(Router);
    const http = inject(HttpClient);
    const searchSubject = new Subject<string>();

    const loadLibrary = rxMethod<void>(
      switchMap(() => {
        patchState(store, { isLoading: true, error: null });

        // Get current search criteria
        const criteria = {
          searchQuery: store.searchQuery(),
          tags: store.selectedTags(),
        };

        return libraryService.browse(criteria).pipe(
          tapResponse({
            next: (items) => {
              patchState(store, { items, isLoading: false });
            },
            error: () => {
              patchState(store, { 
                error: 'Failed to load library items', 
                isLoading: false 
              });
            },
          })
        );
      })
    );

    const loadTags = rxMethod<void>(
      switchMap(() => {
        return libraryService.getTags().pipe(
          tapResponse({
            next: (tags) => {
              patchState(store, { tags });
            },
            error: () => {
              // Silently fail - tags are not critical
            },
          })
        );
      })
    );

    return {
      loadLibrary,

      loadTags,

      search(query: string): void {
        searchSubject.next(query);
      },

      setupSearch: rxMethod<void>(() =>
        searchSubject.pipe(
          debounceTime(300),
          distinctUntilChanged(),
          tap((query) => {
            patchState(store, { searchQuery: query });
            // Trigger a new library load with the search query
            loadLibrary(undefined);
          })
        )
      ),

      toggleTag(tagSlug: string): void {
        const currentTags = store.selectedTags();
        const newTags = currentTags.includes(tagSlug)
          ? currentTags.filter((t) => t !== tagSlug)
          : [...currentTags, tagSlug];
        
        patchState(store, { selectedTags: newTags });
        // Reload library with new tag filters
        loadLibrary(undefined);
      },

      clearFilters(): void {
        patchState(store, { 
          searchQuery: '', 
          selectedTags: [] 
        });
        // Reload library without filters
        loadLibrary(undefined);
      },

      setSortBy(sortBy: 'date' | 'title' | 'size'): void {
        const currentSortBy = store.sortBy();
        const currentSortOrder = store.sortOrder();
        
        // Toggle order if same field clicked
        const sortOrder = sortBy === currentSortBy && currentSortOrder === 'desc' 
          ? 'asc' 
          : 'desc';
        
        patchState(store, { sortBy, sortOrder });
      },

      selectItem(item: LibraryItem): void {
        patchState(store, { selectedItem: item, showModal: true });
      },

      closeModal(): void {
        patchState(store, { selectedItem: null, showModal: false });
      },

      confirmDelete(id: string): void {
        patchState(store, { deleteTargetId: id, showDeleteModal: true });
      },

      cancelDelete(): void {
        patchState(store, { deleteTargetId: null, showDeleteModal: false });
      },

      deleteDocument: rxMethod<void>(
        switchMap(() => {
          const targetId = store.deleteTargetId();
          if (!targetId) return [];

          const item = store.items().find(i => i.id === targetId);
          if (!item) return [];

          patchState(store, { isLoading: true });

          return libraryService.deleteDocument(item.documentId).pipe(
            tapResponse({
              next: () => {
                // Remove from local state
                const newItems = store.items().filter(i => i.id !== targetId);
                patchState(store, { 
                  items: newItems,
                  isLoading: false,
                  deleteTargetId: null,
                  showDeleteModal: false
                });
                // Reload tags as counts may have changed
                loadTags(undefined);
                uiStore.showSuccess('Document deleted successfully');
              },
              error: () => {
                patchState(store, { 
                  error: 'Failed to delete document',
                  isLoading: false 
                });
              },
            })
          );
        })
      ),

      exportSummary: rxMethod<{ summaryId: string; format: 'markdown' | 'pdf' | 'text' }>(
        switchMap(({ summaryId, format }) => {
          return summaryService.export(summaryId, format).pipe(
            tapResponse({
              next: (blob) => {
                // Create download link
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `summary.${format}`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                uiStore.showSuccess('Summary exported successfully');
              },
              error: () => {
                uiStore.showError('Failed to export summary');
              },
            })
          );
        })
      ),

      downloadDocument: rxMethod<string>(
        switchMap((documentId) => {
          return documentService.getDownloadUrl(documentId).pipe(
            switchMap((response) => {
              if (!response.url) {
                return of(null);
              }
              
              // Use HttpClient to download with authentication
              return http.get(response.url, { 
                responseType: 'blob',
                observe: 'response' 
              }).pipe(
                tapResponse({
                  next: (httpResponse) => {
                    // Get filename from Content-Disposition header if available
                    const contentDisposition = httpResponse.headers.get('Content-Disposition');
                    let finalFilename = response.filename || 'document';
                    
                    if (contentDisposition) {
                      const filenameMatch = contentDisposition.match(/filename="?(.+?)"?$/);
                      if (filenameMatch) {
                        finalFilename = filenameMatch[1];
                      }
                    }
                    
                    // Create download link
                    const blob = httpResponse.body;
                    if (blob) {
                      const a = document.createElement('a');
                      const url = window.URL.createObjectURL(blob);
                      a.href = url;
                      a.download = finalFilename;
                      document.body.appendChild(a);
                      a.click();
                      document.body.removeChild(a);
                      window.URL.revokeObjectURL(url);
                      uiStore.showSuccess('Document downloaded successfully');
                    }
                  },
                  error: () => {
                    uiStore.showError('Failed to download file');
                  }
                })
              );
            }),
            tapResponse({
              next: () => {
                // Success already handled in inner observable
              },
              error: () => {
                uiStore.showError('Failed to get download URL');
              }
            })
          );
        })
      ),

      startChat: rxMethod<{ documentId: string; filename: string }>(
        switchMap(({ documentId, filename }) => {
          const title = `Chat with ${filename}`;
          return chatService.findOrCreateSession(documentId, title).pipe(
            tapResponse({
              next: (session) => {
                router.navigate(['/app/chat', session.id]);
              },
              error: () => {
                uiStore.showError('Failed to start chat');
              },
            })
          );
        })
      ),

      clearError(): void {
        patchState(store, { error: null });
      },
    };
  }),
  withHooks({
    onInit(store) {
      store.setupSearch(undefined);
      store.loadLibrary(undefined);
      store.loadTags(undefined);
    },
  })
);