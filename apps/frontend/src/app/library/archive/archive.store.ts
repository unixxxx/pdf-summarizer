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

import { ArchiveService } from './archive.service';
import { UIStore } from '../../shared/ui.store';
import { LibraryStore } from '../library.store';
import {
  ArchiveStats,
  ArchivedDocument,
  ArchivedFolderWithChildren,
} from './archive.model';

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

interface EmptyArchiveApiRequest {
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

export interface ArchiveState {
  stats: ArchiveStats | null;
  archivedFolders: ArchivedFolderWithChildren[];
  archivedDocuments: ArchivedDocument[];
  loading: boolean;
  error: string | null;
}

const initialState: ArchiveState = {
  stats: null,
  archivedFolders: [],
  archivedDocuments: [],
  loading: false,
  error: null,
};

export const ArchiveStore = signalStore(
  { providedIn: 'root' },
  withState(initialState),
  withComputed((store) => ({
    isEmpty: computed(
      () =>
        store.archivedFolders().length === 0 &&
        store.archivedDocuments().length === 0
    ),
    hasContent: computed(
      () =>
        store.archivedFolders().length > 0 ||
        store.archivedDocuments().length > 0
    ),
    canEmpty: computed(() => {
      const stats = store.stats();
      return stats && (stats.total_documents > 0 || stats.total_folders > 0);
    }),
  })),

  withMethods((store) => {
    const archiveService = inject(ArchiveService);
    const uiStore = inject(UIStore);
    const libraryStore = inject(LibraryStore);

    const methods = {
      // Load archive content
      loadArchiveContent: rxMethod<void>(
        pipe(
          tap(() => patchState(store, { loading: true, error: null })),
          switchMap(() =>
            forkJoin({
              stats: archiveService.getArchiveStats(),
              folders: archiveService.getArchivedFolders(),
              documents: archiveService.getArchivedDocuments(),
            }).pipe(
              tapResponse({
                next: ({ stats, folders, documents }) => {
                  patchState(store, {
                    stats,
                    archivedFolders: folders,
                    archivedDocuments: documents,
                    loading: false,
                    error: null,
                  });
                },
                error: (error: Error) => {
                  patchState(store, {
                    loading: false,
                    error: error.message || 'Failed to load archive content',
                  });
                  uiStore.showError('Failed to load archive content');
                },
              })
            )
          )
        )
      ),

      // Restore folder
      restoreFolder: rxMethod<ArchivedFolderWithChildren>(
        switchMap((folder) => {
          const request: RestoreFolderApiRequest = {
            folder_id: folder.id,
            restore_children: true,
            new_parent_id: null,
          };

          return archiveService.restoreFolder(request).pipe(
            tapResponse({
              next: () => {
                uiStore.showSuccess(`Folder "${folder.name}" restored`);
                // Reload archive content
                methods.loadArchiveContent();
                // Reload library folders
                // libraryStore.loadFolders();
              },
              error: () => uiStore.showError('Failed to restore folder'),
            })
          );
        })
      ),

      // Restore document
      restoreDocument: rxMethod<ArchivedDocument>(
        switchMap((doc) => {
          // Don't send folder_id if the document is being restored from a deleted folder
          // It will be restored to root level instead
          const request: RestoreDocumentApiRequest = {
            document_ids: [doc.id],
            folder_id: null, // Always restore to root for now
          };

          return archiveService.restoreDocuments(request).pipe(
            tapResponse({
              next: () => {
                uiStore.showSuccess(`Document "${doc.name}" restored to root`);
                // Reload archive content
                methods.loadArchiveContent();
                // Reload library documents
                libraryStore.loadDocuments();
              },
              error: () => uiStore.showError('Failed to restore document'),
            })
          );
        })
      ),

      // Empty archive
      emptyArchive: rxMethod<void>(
        switchMap(() => {
          const request: EmptyArchiveApiRequest = {
            confirm: true,
            delete_all: true,
          };

          return archiveService.emptyArchive(request).pipe(
            tapResponse({
              next: () => {
                uiStore.showSuccess('Archive emptied successfully');
                // Reload archive content
                methods.loadArchiveContent();
              },
              error: () => uiStore.showError('Failed to empty archive'),
            })
          );
        })
      ),

      // Delete document permanently
      deleteDocument: rxMethod<ArchivedDocument>(
        switchMap((doc) => {
          const request: DeleteDocumentsApiRequest = {
            document_ids: [doc.id],
            confirm: true,
          };

          return archiveService.deleteDocuments(request).pipe(
            tapResponse({
              next: () => {
                uiStore.showSuccess(
                  `Document "${doc.name}" permanently deleted`
                );
                // Reload archive content
                methods.loadArchiveContent();
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
      deleteFolder: rxMethod<ArchivedFolderWithChildren>(
        switchMap((folder) => {
          const request: DeleteFolderApiRequest = {
            folder_id: folder.id,
            delete_children: true,
            confirm: true,
          };

          return archiveService.deleteFolder(request).pipe(
            tapResponse({
              next: () => {
                uiStore.showSuccess(
                  `Folder "${folder.name}" permanently deleted`
                );
                // Reload archive content
                methods.loadArchiveContent();
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
