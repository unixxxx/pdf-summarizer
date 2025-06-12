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
import { pipe, switchMap, tap, forkJoin } from 'rxjs';

import { TrashService } from './trash.service';
import { UIStore } from '../../shared/ui.store';
import { LibraryStore } from '../library.store';
import {
  TrashStats,
  TrashedDocument,
  TrashedFolderWithChildren,
} from './trash.model';

// API request interfaces with snake_case for backend compatibility
interface RestoreFolderApiRequest {
  folder_id: string;
  restore_children: boolean;
  new_parent_id: string | null;
}

interface RestoreDocumentApiRequest {
  document_ids: string[];
  folder_id: string | null;
}

interface EmptyTrashApiRequest {
  confirm: boolean;
  delete_all: boolean;
}

interface DeleteDocumentsApiRequest {
  document_ids: string[];
  confirm: boolean;
}

interface DeleteFolderApiRequest {
  folder_id: string;
  delete_children: boolean;
  confirm: boolean;
}

export interface TrashState {
  stats: TrashStats | null;
  trashedFolders: TrashedFolderWithChildren[];
  trashedDocuments: TrashedDocument[];
  loading: boolean;
  error: string | null;
}

const initialState: TrashState = {
  stats: null,
  trashedFolders: [],
  trashedDocuments: [],
  loading: false,
  error: null,
};

export const TrashStore = signalStore(
  { providedIn: 'root' },
  withState(initialState),
  withComputed((store) => ({
    isEmpty: computed(
      () =>
        store.trashedFolders().length === 0 &&
        store.trashedDocuments().length === 0
    ),
    hasContent: computed(
      () =>
        store.trashedFolders().length > 0 || store.trashedDocuments().length > 0
    ),
    canEmpty: computed(() => {
      const stats = store.stats();
      return stats && (stats.total_documents > 0 || stats.total_folders > 0);
    }),
  })),

  withMethods((store) => {
    const trashService = inject(TrashService);
    const uiStore = inject(UIStore);
    const libraryStore = inject(LibraryStore);

    const methods = {
      // Load trash content
      loadTrashContent: rxMethod<void>(
        pipe(
          tap(() => patchState(store, { loading: true, error: null })),
          switchMap(() =>
            forkJoin({
              stats: trashService.getTrashStats(),
              folders: trashService.getTrashedFolders(),
              documents: trashService.getTrashedDocuments(),
            }).pipe(
              tapResponse({
                next: ({ stats, folders, documents }) => {
                  patchState(store, {
                    stats,
                    trashedFolders: folders,
                    trashedDocuments: documents,
                    loading: false,
                    error: null,
                  });
                },
                error: (error: Error) => {
                  patchState(store, {
                    loading: false,
                    error: error.message || 'Failed to load trash content',
                  });
                  uiStore.showError('Failed to load trash content');
                },
              })
            )
          )
        )
      ),

      // Restore folder
      restoreFolder: rxMethod<TrashedFolderWithChildren>(
        switchMap((folder) => {
          const request: RestoreFolderApiRequest = {
            folder_id: folder.id,
            restore_children: true,
            new_parent_id: null,
          };

          return trashService.restoreFolder(request).pipe(
            tapResponse({
              next: () => {
                uiStore.showSuccess(`Folder "${folder.name}" restored`);
                // Reload trash content
                methods.loadTrashContent();
                // Reload library folders
                libraryStore.loadFolders();
              },
              error: () => uiStore.showError('Failed to restore folder'),
            })
          );
        })
      ),

      // Restore document
      restoreDocument: rxMethod<TrashedDocument>(
        switchMap((doc) => {
          // Don't send folder_id if the document is being restored from a deleted folder
          // It will be restored to root level instead
          const request: RestoreDocumentApiRequest = {
            document_ids: [doc.id],
            folder_id: null, // Always restore to root for now
          };

          return trashService.restoreDocuments(request).pipe(
            tapResponse({
              next: () => {
                uiStore.showSuccess(`Document "${doc.name}" restored to root`);
                // Reload trash content
                methods.loadTrashContent();
                // Reload library documents
                libraryStore.loadDocuments();
              },
              error: () => uiStore.showError('Failed to restore document'),
            })
          );
        })
      ),

      // Empty trash
      emptyTrash: rxMethod<void>(
        switchMap(() => {
          const request: EmptyTrashApiRequest = {
            confirm: true,
            delete_all: true,
          };

          return trashService.emptyTrash(request).pipe(
            tapResponse({
              next: () => {
                uiStore.showSuccess('Trash emptied successfully');
                // Reload trash content
                methods.loadTrashContent();
              },
              error: () => uiStore.showError('Failed to empty trash'),
            })
          );
        })
      ),

      // Delete document permanently
      deleteDocument: rxMethod<TrashedDocument>(
        switchMap((doc) => {
          const request: DeleteDocumentsApiRequest = {
            document_ids: [doc.id],
            confirm: true,
          };

          return trashService.deleteDocuments(request).pipe(
            tapResponse({
              next: () => {
                uiStore.showSuccess(`Document "${doc.name}" permanently deleted`);
                // Reload trash content
                methods.loadTrashContent();
              },
              error: (error: Error) => {
                console.error('Delete document error:', error);
                uiStore.showError('Failed to delete document');
              },
            })
          );
        })
      ),

      // Delete folder permanently
      deleteFolder: rxMethod<TrashedFolderWithChildren>(
        switchMap((folder) => {
          const request: DeleteFolderApiRequest = {
            folder_id: folder.id,
            delete_children: true,
            confirm: true,
          };

          return trashService.deleteFolder(request).pipe(
            tapResponse({
              next: () => {
                uiStore.showSuccess(`Folder "${folder.name}" permanently deleted`);
                // Reload trash content
                methods.loadTrashContent();
              },
              error: (error: Error) => {
                console.error('Delete folder error:', error);
                uiStore.showError('Failed to delete folder');
              },
            })
          );
        })
      ),
    };

    return methods;
  })
);
