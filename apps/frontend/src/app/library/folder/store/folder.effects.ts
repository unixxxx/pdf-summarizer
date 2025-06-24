import { inject, Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { switchMap, map, from } from 'rxjs';
import { FolderActions } from './folder.actions';
import { FolderService } from '../services/folder.service';
import { concatLatestFrom, mapResponse } from '@ngrx/operators';
import { TagService } from '../../tag/services/tag.service';
import { UIStore } from '../../../shared/ui.store';
import { ModalService } from '../../../core/services/modal';
import { FolderCreate } from '../components/folder-create';
import { FolderEdit } from '../components/folder-edit';
import { ConfirmDialog } from '../../../shared/components/confirm-dialog/confirm-dialog';
import { FolderCreateDto, FolderUpdateDto } from '../dtos/folder';
import { folderFeature } from './folder.feature';
import { unwrapAsyncDataItem } from '../../../core/utils/async-data-item';
import { FolderItem } from './state/folder';
import { tagFeature } from '../../tag/store/tag.feature';

@Injectable()
export class FolderEffects {
  actions$ = inject(Actions);
  store = inject(Store);
  folderService = inject(FolderService);
  tagService = inject(TagService);
  uiStore = inject(UIStore);
  modalService = inject(ModalService);

  fetchFolders$ = createEffect(() =>
    this.actions$.pipe(
      ofType(FolderActions.fetchFoldersCommand),
      switchMap(() =>
        this.folderService.getFoldersTree().pipe(
          mapResponse({
            next: (folder) =>
              FolderActions.fetchFoldersSuccessEvent({ folder }),
            error: (error: Error) =>
              FolderActions.fetchFoldersFailureEvent({ error: error.message }),
          })
        )
      )
    )
  );

  // Folder CRUD operations
  createFolder$ = createEffect(() =>
    this.actions$.pipe(
      ofType(FolderActions.createFolderCommand),
      switchMap(({ request }) =>
        this.folderService.createFolder(request).pipe(
          mapResponse({
            next: (folder) => {
              this.uiStore.showNotification(
                'Folder created successfully',
                'success'
              );
              return FolderActions.createFolderSuccessEvent({ folder });
            },
            error: (error: Error) => {
              this.uiStore.showNotification('Failed to create folder', 'error');
              return FolderActions.createFolderFailureEvent({
                error: error.message,
              });
            },
          })
        )
      )
    )
  );

  updateFolder$ = createEffect(() =>
    this.actions$.pipe(
      ofType(FolderActions.updateFolderCommand),
      switchMap(({ id, request }) =>
        this.folderService.updateFolder(id, request).pipe(
          mapResponse({
            next: (folder) => {
              this.uiStore.showNotification(
                'Folder updated successfully',
                'success'
              );
              return FolderActions.updateFolderSuccessEvent({ folder });
            },
            error: (error: Error) => {
              this.uiStore.showNotification('Failed to update folder', 'error');
              return FolderActions.updateFolderFailureEvent({
                error: error.message,
              });
            },
          })
        )
      )
    )
  );

  deleteFolder$ = createEffect(() =>
    this.actions$.pipe(
      ofType(FolderActions.deleteFolderCommand),
      switchMap(({ id }) =>
        this.folderService.deleteFolder(id).pipe(
          mapResponse({
            next: () => {
              this.uiStore.showNotification(
                'Folder deleted successfully',
                'success'
              );
              return FolderActions.deleteFolderSuccessEvent({ id });
            },
            error: (error: Error) => {
              this.uiStore.showNotification('Failed to delete folder', 'error');
              return FolderActions.deleteFolderFailureEvent({
                error: error.message,
              });
            },
          })
        )
      )
    )
  );

  // Handle create folder modal
  openCreateFolderModal$ = createEffect(() =>
    this.actions$.pipe(
      ofType(FolderActions.openCreateFolderModalCommand),
      concatLatestFrom(() => [
        this.store.select(folderFeature.selectFolder),
        this.store.select(tagFeature.selectTags),
      ]),
      switchMap(([{ parentId }, asyncFolders, asyncTags]) => {
        const folderData = unwrapAsyncDataItem(asyncFolders);
        return from(
          this.modalService.create<FolderCreateDto>({
            component: FolderCreate,
            inputs: {
              parentId,
              folders: folderData.folders,
              tags: unwrapAsyncDataItem(asyncTags),
            },
            cssClass: 'folder-modal',
            backdropDismiss: true,
            keyboardClose: true,
          })
        ).pipe(
          switchMap((modalRef) =>
            from(modalRef.onDidDismiss()).pipe(
              map((result) => {
                if (result.role === 'create' && result.data) {
                  return FolderActions.createFolderCommand({
                    request: result.data,
                  });
                }
                // No action needed when modal is cancelled
                return { type: '@ngrx/no-op' };
              })
            )
          )
        );
      })
    )
  );

  // Handle edit folder modal
  openEditFolderModal$ = createEffect(() =>
    this.actions$.pipe(
      ofType(FolderActions.openEditFolderModalCommand),
      concatLatestFrom(() => [
        this.store.select(folderFeature.selectFolder),
        this.store.select(tagFeature.selectTags),
      ]),
      switchMap(([{ folder }, asyncFolders, asyncTags]) => {
        const folderData = unwrapAsyncDataItem(asyncFolders);

        // Find the original folder in the tree to get the clean name
        const findOriginalFolder = (
          folders: FolderItem[],
          id: string
        ): FolderItem | null => {
          for (const f of folders) {
            if (f.id === id) return f;
            if (f.children) {
              const found = findOriginalFolder(f.children, id);
              if (found) return found;
            }
          }
          return null;
        };

        const originalFolder =
          findOriginalFolder(folderData.folders, folder.id) || folder;

        return from(
          this.modalService.create<FolderUpdateDto>({
            component: FolderEdit,
            inputs: {
              folder: originalFolder,
              folders: folderData.folders,
              tags: unwrapAsyncDataItem(asyncTags),
            },
            cssClass: 'folder-modal',
            backdropDismiss: true,
            keyboardClose: true,
          })
        ).pipe(
          switchMap((modalRef) =>
            from(modalRef.onDidDismiss()).pipe(
              map((result) => {
                if (result.role === 'update' && result.data) {
                  return FolderActions.updateFolderCommand({
                    id: folder.id,
                    request: result.data,
                  });
                }
                // No action needed when modal is cancelled
                return { type: '@ngrx/no-op' };
              })
            )
          )
        );
      })
    )
  );

  // Handle delete folder modal
  openDeleteFolderModal$ = createEffect(() =>
    this.actions$.pipe(
      ofType(FolderActions.openDeleteFolderModalCommand),
      switchMap(({ folder }) => {
        const hasContents =
          folder.documentCount > 0 || folder.children?.length > 0;
        const contentsList = [];
        if (folder.documentCount > 0) {
          contentsList.push(
            `${folder.documentCount} document${
              folder.documentCount > 1 ? 's' : ''
            }`
          );
        }
        if (folder.children?.length > 0) {
          contentsList.push(
            `${folder.children.length} subfolder${
              folder.children.length > 1 ? 's' : ''
            }`
          );
        }

        const message = hasContents
          ? `Are you sure you want to delete the folder "${
              folder.name
            }"? It contains ${contentsList.join(
              ' and '
            )}. All contents will be permanently deleted.`
          : `Are you sure you want to delete the folder "${folder.name}"? This action cannot be undone.`;

        return from(
          this.modalService.create<boolean>({
            component: ConfirmDialog,
            inputs: {
              title: 'Delete Folder',
              message,
              confirmText: 'Delete Folder',
              cancelText: 'Cancel',
            },
            cssClass: 'delete-modal',
            backdropDismiss: true,
            keyboardClose: true,
          })
        ).pipe(
          switchMap((modalRef) =>
            from(modalRef.onDidDismiss()).pipe(
              map((result) => {
                if (result.role === 'confirm') {
                  return FolderActions.deleteFolderCommand({ id: folder.id });
                }
                // No action needed when modal is cancelled
                return { type: '@ngrx/no-op' };
              })
            )
          )
        );
      })
    )
  );
}
