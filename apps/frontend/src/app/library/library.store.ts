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

import { FolderService } from './folders/folder.service';
import { DocumentService, DocumentSearchCriteria } from './documents/document.service';
import { TagService } from './tags/tag.service';
import { UIStore } from '../shared/ui.store';

import {
  FolderWithChildren,
  CreateFolderRequest,
  UpdateFolderRequest,
} from './folders/folder.model';
import { LibraryItem } from './documents/document.model';
import { Tag } from './tags/tag.model';

// Dialog data types
interface FolderDialogData {
  folder: FolderWithChildren | null;
  form: {
    name: string;
    description: string;
    color: string;
    parentId?: string | null;
  };
}

type DialogData = FolderDialogData | FolderWithChildren | LibraryItem;

// Simplified state structure with logical groupings
export interface LibraryState {
  // Core data
  folders: FolderWithChildren[];
  documents: LibraryItem[];
  tags: Tag[];
  
  // UI Navigation
  selectedFolderId: string | null;
  expandedFolders: string[];
  
  // Search & Filter
  searchQuery: string;
  selectedTags: string[];
  
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
  folders: [],
  documents: [],
  tags: [],
  selectedFolderId: null,
  expandedFolders: [],
  searchQuery: '',
  selectedTags: [],
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
      Object.values(store.loading()).some(loading => loading)
    ),
    
    documentsIsEmpty: computed(() => store.documents().length === 0),
    documentsHasError: computed(() => store.errors().documents !== null),
    documentsIsSearching: computed(() => 
      store.searchQuery().length > 0 || store.selectedTags().length > 0
    ),
    
    tagsIsEmpty: computed(() => store.tags().length === 0),
    popularTags: computed(() => 
      [...store.tags()].sort((a, b) => (b.documentCount || 0) - (a.documentCount || 0))
    ),
    
    // Dialog helpers
    isDialogOpen: computed(() => store.dialog().type !== null),
    dialogType: computed(() => store.dialog().type),
    dialogData: computed(() => store.dialog().data),
    
    // Specific dialog states for components
    showFolderDialog: computed(() => store.dialog().type === 'folder'),
    editingFolder: computed(() => 
      store.dialog().type === 'folder' ? (store.dialog().data as FolderDialogData)?.folder : null
    ),
    showDeleteFolderConfirm: computed(() => store.dialog().type === 'deleteFolder'),
    deletingFolder: computed(() => 
      store.dialog().type === 'deleteFolder' ? store.dialog().data as FolderWithChildren : null
    ),
    showDeleteDocumentConfirm: computed(() => store.dialog().type === 'deleteDocument'),
    deletingDocument: computed(() => 
      store.dialog().type === 'deleteDocument' ? store.dialog().data as LibraryItem : null
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
    
    // Constants
    availableColors: computed(() => [
      '#6B7280', '#EF4444', '#F59E0B', '#10B981',
      '#3B82F6', '#6366F1', '#8B5CF6', '#EC4899',
    ]),
  })),
  
  withMethods((store) => {
    const folderService = inject(FolderService);
    const documentService = inject(DocumentService);
    const tagService = inject(TagService);
    const uiStore = inject(UIStore);
    
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
    const openDialog = (type: LibraryState['dialog']['type'], data: DialogData | null = null) => {
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
    ) => rxMethod<string>(
      switchMap((id) =>
        serviceFn(id).pipe(
          tapResponse({
            next: () => {
              handleSuccess(successMessage);
              closeDialog();
              afterDelete?.();
            },
            error: () => handleError(`Failed to ${successMessage.toLowerCase()}`),
          })
        )
      )
    );
    
    // Loading state helpers
    const setLoading = (key: keyof LibraryState['loading'], value: boolean) => {
      patchState(store, {
        loading: { ...store.loading(), [key]: value }
      });
    };
    
    // Data loading methods
    const loadFolders = rxMethod<void>(
      switchMap(() => {
        setLoading('folders', true);
        return folderService.getFoldersTree().pipe(
          tapResponse({
            next: (tree) => {
              patchState(store, {
                folders: tree.folders,
                counts: {
                  ...store.counts(),
                  total: tree.totalDocumentCount || tree.total_document_count || 0,
                  unfiled: tree.unfiledCount || tree.unfiled_count || 0,
                },
                loading: { ...store.loading(), folders: false },
              });
            },
            error: () => {
              setLoading('folders', false);
              handleError('Failed to load folders');
            },
          })
        );
      })
    );
    
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
            tags: store.selectedTags(),
            folderId: (() => {
              const folderId = store.selectedFolderId();
              return folderId && folderId !== 'unfiled' ? folderId : undefined;
            })(),
            unfiled: store.selectedFolderId() === 'unfiled',
            limit: store.pagination().limit,
            offset: 0,
          };
          return documentService.browse(criteria).pipe(
            tapResponse({
              next: (response) => {
                const items = response.items.map(dto => LibraryItem.fromDto(dto));
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
    
    const loadTags = rxMethod<void>(
      pipe(
        tap(() => setLoading('tags', true)),
        switchMap(() =>
          tagService.findAll().pipe(
            tapResponse({
              next: (tags) => patchState(store, { 
                tags, 
                loading: { ...store.loading(), tags: false } 
              }),
              error: () => setLoading('tags', false),
            })
          )
        )
      )
    );
    
    // Folder operations
    const deleteFolder = createDeleteMethod(
      (id) => folderService.deleteFolder(id),
      'Folder deleted successfully',
      () => {
        const deletedFolder = store.dialog().data as FolderWithChildren;
        if (deletedFolder && store.selectedFolderId() === deletedFolder.id) {
          patchState(store, { selectedFolderId: null });
        }
        loadFolders(undefined);
        loadDocuments(undefined);
      }
    );
    
    // Document operations
    const deleteDocument = createDeleteMethod(
      (id) => documentService.delete(id),
      'Document deleted successfully',
      () => {
        const deletedDoc = store.dialog().data as LibraryItem;
        if (deletedDoc) {
          patchState(store, {
            documents: store.documents().filter(d => d.documentId !== deletedDoc.documentId),
            counts: { ...store.counts(), documentsTotal: store.counts().documentsTotal - 1 },
          });
        }
        loadFolders(undefined);
        loadTags(undefined);
      }
    );
    
    return {
      // Initialization
      initialize(): void {
        loadFolders(undefined);
        loadDocuments(undefined);
        loadTags(undefined);
      },
      
      // Data loading
      loadFolders,
      loadDocuments,
      loadTags,
      
      // Navigation
      selectFolder(folderId: string | null): void {
        patchState(store, { selectedFolderId: folderId });
        loadDocuments(undefined);
      },
      
      toggleFolderExpanded(folderId: string): void {
        const expanded = store.expandedFolders();
        patchState(store, {
          expandedFolders: expanded.includes(folderId)
            ? expanded.filter(id => id !== folderId)
            : [...expanded, folderId]
        });
      },
      
      // Search & Filter
      setSearchQuery(searchQuery: string): void {
        patchState(store, { searchQuery });
      },
      
      setSelectedTags(tags: string[]): void {
        patchState(store, { selectedTags: tags });
      },
      
      toggleTag(tag: string): void {
        const currentTags = store.selectedTags();
        patchState(store, {
          selectedTags: currentTags.includes(tag)
            ? currentTags.filter(t => t !== tag)
            : [...currentTags, tag]
        });
      },
      
      clearFilters(): void {
        patchState(store, { 
          searchQuery: '', 
          selectedTags: [], 
          selectedFolderId: null 
        });
      },
      
      // Dialog management
      showNewFolderDialog(): void {
        openDialog('folder', {
          folder: null,
          form: { name: '', description: '', color: '#6B7280', parentId: null }
        });
      },
      
      showEditFolderDialog(folder: FolderWithChildren): void {
        openDialog('folder', {
          folder,
          form: {
            name: folder.name,
            description: folder.description || '',
            color: folder.color || '#6B7280',
            parentId: folder.parentId || folder.parent_id || null,
          }
        });
      },
      
      closeFolderDialog(): void {
        closeDialog();
      },
      
      confirmDeleteFolder(folder: FolderWithChildren): void {
        openDialog('deleteFolder', folder);
      },
      
      confirmDeleteDocument(document: LibraryItem): void {
        openDialog('deleteDocument', document);
      },
      
      cancelDeleteFolder(): void {
        closeDialog();
      },
      
      cancelDeleteDocument(): void {
        closeDialog();
      },
      
      executeDeleteFolder(): void {
        const folder = store.dialog().data as FolderWithChildren;
        if (folder?.id) {
          deleteFolder(folder.id);
        }
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
        this.addDocumentsToFolder({ folderId, documentIds: [documentId] });
      },
      
      // Tag operations
      updateTag: rxMethod<{ tagId: string; updates: { name: string; color: string } }>(
        switchMap(({ tagId, updates }) =>
          tagService.update(tagId, updates).pipe(
            tapResponse({
              next: () => {
                handleSuccess('Tag updated successfully');
                loadTags(undefined);
              },
              error: () => handleError('Failed to update tag'),
            })
          )
        )
      ),
      
      deleteTag: rxMethod<string>(
        switchMap((tagId) =>
          tagService.delete(tagId).pipe(
            tapResponse({
              next: () => {
                handleSuccess('Tag deleted successfully');
                loadTags(undefined);
                loadDocuments(undefined);
              },
              error: () => handleError('Failed to delete tag'),
            })
          )
        )
      ),
      
      // Additional helper methods that were missing
      folderForm: computed(() => {
        const data = store.dialog().data as FolderDialogData;
        return data?.form || { name: '', description: '', color: '#6B7280', parentId: null };
      }),
      
      updateFolderForm(updates: Record<string, unknown>): void {
        if (store.dialog().type === 'folder') {
          const currentData = store.dialog().data as FolderDialogData;
          const newData: FolderDialogData = {
            folder: currentData?.folder || null,
            form: {
              ...currentData?.form,
              ...updates
            } as FolderDialogData['form']
          };
          patchState(store, {
            dialog: {
              type: 'folder',
              data: newData
            }
          });
        }
      },
      
      // Folder CRUD operations
      createFolder: rxMethod<CreateFolderRequest>(
        switchMap((request) =>
          folderService.createFolder(request).pipe(
            tapResponse({
              next: () => {
                handleSuccess('Folder created successfully');
                closeDialog();
                loadFolders(undefined);
              },
              error: () => handleError('Failed to create folder'),
            })
          )
        )
      ),
      
      updateFolder: rxMethod<{ id: string; update: UpdateFolderRequest }>(
        switchMap(({ id, update }) =>
          folderService.updateFolder(id, update).pipe(
            tapResponse({
              next: () => {
                handleSuccess('Folder updated successfully');
                closeDialog();
                loadFolders(undefined);
              },
              error: () => handleError('Failed to update folder'),
            })
          )
        )
      ),
      
      saveFolder(): void {
        const dialogData = store.dialog().data as FolderDialogData;
        if (!dialogData) return;
        
        const { folder, form } = dialogData;
        if (folder) {
          this.updateFolder({
            id: folder.id,
            update: {
              name: form.name,
              description: form.description || undefined,
              color: form.color,
              parentId: form.parentId,
            },
          });
        } else {
          this.createFolder({
            name: form.name,
            description: form.description || undefined,
            color: form.color,
            parentId: form.parentId || undefined,
          });
        }
      },
      
      addDocumentsToFolder: rxMethod<{ folderId: string; documentIds: string[] }>(
        switchMap(({ folderId, documentIds }) =>
          folderService.addDocumentsToFolder(folderId, { documentIds }).pipe(
            tapResponse({
              next: () => {
                const folder = store.folders().find(f => f.id === folderId);
                handleSuccess(`Document moved to ${folder?.name || 'folder'}`);
                loadFolders(undefined);
                loadDocuments(undefined);
              },
              error: () => handleError('Failed to move document'),
            })
          )
        )
      ),
      
      // Document operations
      loadMoreDocuments: rxMethod<void>(
        pipe(
          tap(() => {
            if (store.loading().documentsMore || !store.pagination().hasMore) return;
            setLoading('documentsMore', true);
          }),
          switchMap(() => {
            if (store.loading().documentsMore || !store.pagination().hasMore) return of(null);
            
            const newOffset = store.pagination().offset + store.pagination().limit;
            const criteria: DocumentSearchCriteria = {
              searchQuery: store.searchQuery(),
              tags: store.selectedTags(),
              folderId: (() => {
                const folderId = store.selectedFolderId();
                return folderId && folderId !== 'unfiled' ? folderId : undefined;
              })(),
              unfiled: store.selectedFolderId() === 'unfiled',
              limit: store.pagination().limit,
              offset: newOffset,
            };
            return documentService.browse(criteria).pipe(
              tapResponse({
                next: (response) => {
                  if (response) {
                    const newItems = response.items.map(dto => LibraryItem.fromDto(dto));
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
      
      exportSummary: rxMethod<{ summaryId: string; format: 'pdf' | 'markdown' | 'text' }>(
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
                  errors: { ...store.errors(), documents: error.message }
                }),
            })
          )
        )
      ),
      
      // Helper methods
      getTagById(tagId: string): Tag | undefined {
        return store.tags().find(tag => tag.id === tagId);
      },
      
      getTagBySlug(slug: string): Tag | undefined {
        return store.tags().find(tag => tag.slug === slug);
      },
    };
  })
);