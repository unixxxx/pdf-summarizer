import { inject, computed } from '@angular/core';
import { LibraryService } from './library.service';
import { LibraryItem, Tag } from './library.model';
import { UIStore } from '../shared/ui.store';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { Subject } from 'rxjs';
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
    filteredItems: computed(() => {
      const items = store.items();
      const searchQuery = store.searchQuery().toLowerCase();
      const selectedTags = store.selectedTags();

      let filtered = items;

      // Apply search filter
      if (searchQuery) {
        filtered = filtered.filter(
          (item) =>
            item.filename.toLowerCase().includes(searchQuery) ||
            item.summary.content.toLowerCase().includes(searchQuery) ||
            item.summary.tags.some((tag) => tag.name.toLowerCase().includes(searchQuery))
        );
      }

      // Apply tag filter
      if (selectedTags.length > 0) {
        filtered = filtered.filter((item) =>
          selectedTags.every((tagSlug) =>
            item.summary.tags.some((tag) => tag.slug === tagSlug)
          )
        );
      }

      // Apply sorting
      const sortBy = store.sortBy();
      const sortOrder = store.sortOrder();
      
      const sorted = [...filtered].sort((a, b) => {
        let comparison = 0;
        
        switch (sortBy) {
          case 'title':
            comparison = a.filename.localeCompare(b.filename);
            break;
          case 'size':
            comparison = a.fileSize - b.fileSize;
            break;
          case 'date':
          default:
            comparison = new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
        }
        
        return sortOrder === 'asc' ? comparison : -comparison;
      });

      return sorted;
    }),

    hasActiveFilters: computed(() => {
      return store.searchQuery().length > 0 || store.selectedTags().length > 0;
    }),
  })),
  withMethods((store) => {
    const libraryService = inject(LibraryService);
    const uiStore = inject(UIStore);
    const searchSubject = new Subject<string>();

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
      loadLibrary: rxMethod<void>(
        switchMap(() => {
          patchState(store, { isLoading: true, error: null });

          return libraryService.browse().pipe(
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
      ),

      loadTags,

      search(query: string): void {
        searchSubject.next(query);
      },

      setupSearch: rxMethod<void>(() =>
        searchSubject.pipe(
          debounceTime(300),
          distinctUntilChanged(),
          switchMap((query) => {
            patchState(store, { searchQuery: query });
            return [];
          })
        )
      ),

      toggleTag(tagSlug: string): void {
        const currentTags = store.selectedTags();
        const newTags = currentTags.includes(tagSlug)
          ? currentTags.filter((t) => t !== tagSlug)
          : [...currentTags, tagSlug];
        
        patchState(store, { selectedTags: newTags });
      },

      clearFilters(): void {
        patchState(store, { 
          searchQuery: '', 
          selectedTags: [] 
        });
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