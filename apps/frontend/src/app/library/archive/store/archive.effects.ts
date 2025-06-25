import { inject, Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { forkJoin, switchMap, tap, take, mergeMap } from 'rxjs';
import { mapResponse } from '@ngrx/operators';
import { ArchiveActions } from './archive.actions';
import { archiveFeature } from './archive.feature';
import { ArchiveService } from '../services/archive.service';
import { UIStore } from '../../../shared/ui.store';
import { ModalService } from '../../../core/services/modal';
import { ArchiveDeleteDialog } from '../components/archive-delete-dialog';
import { ArchiveEmptyDialog } from '../components/archive-empty-dialog';
import { ArchiveRestoreDialog } from '../components/archive-restore-dialog';

@Injectable()
export class ArchiveEffects {
  private readonly actions$ = inject(Actions);
  private readonly store = inject(Store);
  private readonly archiveService = inject(ArchiveService);
  private readonly uiStore = inject(UIStore);
  private readonly modalService = inject(ModalService);

  fetchArchive$ = createEffect(() =>
    this.actions$.pipe(
      ofType(ArchiveActions.fetchArchiveCommand),
      switchMap(() =>
        forkJoin({
          stats: this.archiveService.getArchiveStats(),
          folders: this.archiveService.getArchivedFolders(),
          documents: this.archiveService.getArchivedDocuments(),
        }).pipe(
          mapResponse({
            next: ({ stats, folders, documents }) =>
              ArchiveActions.fetchArchiveSuccessEvent({
                stats,
                folders,
                documents,
              }),
            error: (error: Error) =>
              ArchiveActions.fetchArchiveFailureEvent({
                error: error.message || 'Failed to load archive content',
              }),
          })
        )
      )
    )
  );

  restoreFolder$ = createEffect(() =>
    this.actions$.pipe(
      ofType(ArchiveActions.restoreFolderCommand),
      switchMap(({ folderId, restoreChildren, newParentId }) =>
        this.archiveService
          .restoreFolder({
            folder_id: folderId,
            restore_children: restoreChildren,
            new_parent_id: newParentId,
          })
          .pipe(
            mapResponse({
              next: () => {
                this.uiStore.showSuccess('Folder restored successfully');
                return ArchiveActions.restoreFolderSuccessEvent({ folderId });
              },
              error: (error: Error) =>
                ArchiveActions.restoreFolderFailureEvent({
                  error: error.message || 'Failed to restore folder',
                }),
            })
          )
      )
    )
  );

  restoreDocument$ = createEffect(() =>
    this.actions$.pipe(
      ofType(ArchiveActions.restoreDocumentCommand),
      switchMap(({ documentIds, folderId }) =>
        this.archiveService
          .restoreDocuments({
            document_ids: documentIds,
            folder_id: folderId,
          })
          .pipe(
            mapResponse({
              next: () => {
                this.uiStore.showSuccess('Document restored successfully');
                return ArchiveActions.restoreDocumentSuccessEvent({
                  documentIds,
                });
              },
              error: (error: Error) =>
                ArchiveActions.restoreDocumentFailureEvent({
                  error: error.message || 'Failed to restore document',
                }),
            })
          )
      )
    )
  );

  deleteFolderPermanently$ = createEffect(() =>
    this.actions$.pipe(
      ofType(ArchiveActions.deleteFolderPermanentlyCommand),
      switchMap(({ folderId, deleteChildren }) =>
        this.archiveService
          .deleteFolder({
            folder_id: folderId,
            delete_children: deleteChildren,
          })
          .pipe(
            mapResponse({
              next: () => {
                this.uiStore.showSuccess('Folder permanently deleted');
                return ArchiveActions.deleteFolderPermanentlySuccessEvent({
                  folderId,
                });
              },
              error: (error: Error) =>
                ArchiveActions.deleteFolderPermanentlyFailureEvent({
                  error: error.message || 'Failed to delete folder',
                }),
            })
          )
      )
    )
  );

  deleteDocumentPermanently$ = createEffect(() =>
    this.actions$.pipe(
      ofType(ArchiveActions.deleteDocumentPermanentlyCommand),
      switchMap(({ documentIds }) =>
        this.archiveService
          .deleteDocuments({
            document_ids: documentIds,
          })
          .pipe(
            mapResponse({
              next: () => {
                this.uiStore.showSuccess('Document permanently deleted');
                return ArchiveActions.deleteDocumentPermanentlySuccessEvent({
                  documentIds,
                });
              },
              error: (error: Error) =>
                ArchiveActions.deleteDocumentPermanentlyFailureEvent({
                  error: error.message || 'Failed to delete document',
                }),
            })
          )
      )
    )
  );

  emptyArchive$ = createEffect(() =>
    this.actions$.pipe(
      ofType(ArchiveActions.emptyArchiveCommand),
      switchMap(() =>
        this.archiveService
          .emptyArchive({
            confirm: true,
            delete_all: true,
          })
          .pipe(
            mapResponse({
              next: () => {
                this.uiStore.showSuccess('Archive emptied successfully');
                return ArchiveActions.emptyArchiveSuccessEvent();
              },
              error: (error: Error) =>
                ArchiveActions.emptyArchiveFailureEvent({
                  error: error.message || 'Failed to empty archive',
                }),
            })
          )
      )
    )
  );

  // Modal effects
  openRestoreFolderModal$ = createEffect(() =>
    this.actions$.pipe(
      ofType(ArchiveActions.openRestoreFolderModalCommand),
      mergeMap(async ({ folder }) => {
        const modalRef = await this.modalService.create({
          component: ArchiveRestoreDialog,
          inputs: {
            itemName: folder.name,
            isFolder: true,
            parentName: folder.parentName,
            documentCount: folder.documentCount,
            childrenCount: folder.childrenCount,
          },
        });

        const result = await modalRef.onDidDismiss();
        if (result.data) {
          return ArchiveActions.restoreFolderCommand({
            folderId: folder.id,
            restoreChildren: true,
            newParentId: null,
          });
        }
        return { type: 'NO_ACTION' };
      })
    )
  );

  openRestoreDocumentModal$ = createEffect(() =>
    this.actions$.pipe(
      ofType(ArchiveActions.openRestoreDocumentModalCommand),
      mergeMap(async ({ document }) => {
        const modalRef = await this.modalService.create({
          component: ArchiveRestoreDialog,
          inputs: {
            itemName: document.name,
            isFolder: false,
            parentName: document.folderName,
            documentCount: 0,
            childrenCount: 0,
          },
        });

        const result = await modalRef.onDidDismiss();
        if (result.data) {
          return ArchiveActions.restoreDocumentCommand({
            documentIds: [document.id],
            folderId: null,
          });
        }
        return { type: 'NO_ACTION' };
      })
    )
  );

  openDeleteFolderModal$ = createEffect(() =>
    this.actions$.pipe(
      ofType(ArchiveActions.openDeleteFolderModalCommand),
      mergeMap(async ({ folder }) => {
        const modalRef = await this.modalService.create({
          component: ArchiveDeleteDialog,
          inputs: {
            itemName: folder.name,
            isFolder: true,
            documentCount: folder.documentCount,
            childrenCount: folder.childrenCount,
          },
        });

        const result = await modalRef.onDidDismiss();
        if (result.data) {
          return ArchiveActions.deleteFolderPermanentlyCommand({
            folderId: folder.id,
            deleteChildren: true,
          });
        }
        return { type: 'NO_ACTION' };
      })
    )
  );

  openDeleteDocumentModal$ = createEffect(() =>
    this.actions$.pipe(
      ofType(ArchiveActions.openDeleteDocumentModalCommand),
      mergeMap(async ({ document }) => {
        const modalRef = await this.modalService.create({
          component: ArchiveDeleteDialog,
          inputs: {
            itemName: document.name,
            isFolder: false,
            documentCount: 0,
            childrenCount: 0,
          },
        });

        const result = await modalRef.onDidDismiss();
        if (result.data) {
          return ArchiveActions.deleteDocumentPermanentlyCommand({
            documentIds: [document.id],
          });
        }
        return { type: 'NO_ACTION' };
      })
    )
  );

  openEmptyArchiveModal$ = createEffect(() =>
    this.actions$.pipe(
      ofType(ArchiveActions.openEmptyArchiveModalCommand),
      switchMap(() =>
        this.store.select(archiveFeature.selectArchiveStats).pipe(
          take(1),
          mergeMap(async (stats) => {
            const modalRef = await this.modalService.create({
              component: ArchiveEmptyDialog,
              inputs: {
                documentCount: stats?.totalDocuments || 0,
                folderCount: stats?.totalFolders || 0,
                totalSize: stats?.totalSize || 0,
              },
            });

            const result = await modalRef.onDidDismiss();
            if (result.data) {
              return ArchiveActions.emptyArchiveCommand();
            }
            return { type: 'NO_ACTION' };
          })
        )
      )
    )
  );

  // Error handling
  handleErrors$ = createEffect(
    () =>
      this.actions$.pipe(
        ofType(
          ArchiveActions.fetchArchiveFailureEvent,
          ArchiveActions.restoreFolderFailureEvent,
          ArchiveActions.restoreDocumentFailureEvent,
          ArchiveActions.deleteFolderPermanentlyFailureEvent,
          ArchiveActions.deleteDocumentPermanentlyFailureEvent,
          ArchiveActions.emptyArchiveFailureEvent
        ),
        tap((action) => {
          this.uiStore.showError(action.error);
        })
      ),
    { dispatch: false }
  );
}
