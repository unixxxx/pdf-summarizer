import { Injectable, inject } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { map, catchError, mergeMap, tap, concatMap } from 'rxjs/operators';
import { of, concat } from 'rxjs';
import { UploadActions } from './upload.actions';
import { UploadService } from '../services/upload.service';
import { ModalService } from '../../../core/services/modal';
import { UploadDialogComponent } from '../components/upload-dialog.component';
import { concatLatestFrom } from '@ngrx/operators';
import { folderFeature } from '../../folder/store/folder.feature';

@Injectable()
export class UploadEffects {
  private actions$ = inject(Actions);
  private uploadService = inject(UploadService);
  private store = inject(Store);
  private modalService = inject(ModalService);

  uploadFile$ = createEffect(() =>
    this.actions$.pipe(
      ofType(UploadActions.uploadFileCommand),
      concatLatestFrom(() =>
        this.store.select(folderFeature.selectSelectedFolderId)
      ),
      mergeMap(([{ file }, folderId]) => {
        const fileId = crypto.randomUUID();

        // First emit the started event, then handle the upload stream
        return concat(
          // Emit the started event first
          of(
            UploadActions.uploadFileStartedEvent({
              fileId,
              fileName: file.name,
            })
          ),
          // Then handle the upload stream
          this.uploadService.uploadFile(file, folderId).pipe(
            map((event) => {
              switch (event.type) {
                case 'progress':
                  return UploadActions.uploadFileProgressEvent({
                    progress: {
                      fileId: event.fileId || fileId,
                      fileName: event.fileName || file.name,
                      progress: event.progress || 0,
                      stage: event.stage,
                    },
                  });
                case 'success':
                  if (!event.result) {
                    return UploadActions.uploadFileFailureEvent({
                      error: 'Upload succeeded but no result returned',
                      fileName: file.name,
                    });
                  }
                  return UploadActions.uploadFileSuccessEvent({
                    result: event.result,
                  });
                case 'error':
                  return UploadActions.uploadFileFailureEvent({
                    error: event.error || 'Upload failed',
                    fileName: file.name,
                  });
                default:
                  return UploadActions.uploadFileProgressEvent({
                    progress: {
                      fileId: event.fileId || fileId,
                      fileName: event.fileName || file.name,
                      progress: 0,
                    },
                  });
              }
            }),
            catchError((error) =>
              of(
                UploadActions.uploadFileFailureEvent({
                  error: error.message || 'Upload failed',
                  fileName: file.name,
                })
              )
            )
          )
        );
      })
    )
  );

  createTextDocument$ = createEffect(() =>
    this.actions$.pipe(
      ofType(UploadActions.createTextDocumentCommand),
      concatLatestFrom(() =>
        this.store.select(folderFeature.selectSelectedFolderId)
      ),
      mergeMap(([{ content, title }, folderId]) =>
        concat(
          // Emit the started event first
          of(
            UploadActions.createTextDocumentStartedEvent({
              fileName: title,
            })
          ),
          // Then handle the document creation
          this.uploadService
            .createTextDocument({ content, title, folder_id: folderId })
            .pipe(
              map((event) => {
                if (event.type === 'success') {
                  if (!event.result) {
                    return UploadActions.createTextDocumentFailureEvent({
                      error: 'Document created but no result returned',
                      fileName: title,
                    });
                  }
                  return UploadActions.createTextDocumentSuccessEvent({
                    result: event.result,
                  });
                } else {
                  return UploadActions.createTextDocumentFailureEvent({
                    error: event.error || 'Failed to create document',
                    fileName: title,
                  });
                }
              }),
              catchError((error) =>
                of(
                  UploadActions.createTextDocumentFailureEvent({
                    error: error.message || 'Failed to create document',
                    fileName: title,
                  })
                )
              )
            )
        )
      )
    )
  );

  // Open upload dialog
  openUploadDialog$ = createEffect(
    () =>
      this.actions$.pipe(
        ofType(UploadActions.openUploadDialogCommand),
        tap(async () => {
          await this.modalService.create({
            component: UploadDialogComponent,
            backdropDismiss: true,
            animated: true,
            cssClass: 'upload-modal',
          });
        })
      ),
    { dispatch: false }
  );

  // Show error notifications
  showErrorNotification$ = createEffect(
    () =>
      this.actions$.pipe(
        ofType(
          UploadActions.uploadFileFailureEvent,
          UploadActions.createTextDocumentFailureEvent
        ),
        tap(() => {
          // TODO: Integrate with a notification service
        })
      ),
    { dispatch: false }
  );

  // Handle successful upload - close modal and reset state
  handleUploadSuccess$ = createEffect(() =>
    this.actions$.pipe(
      ofType(
        UploadActions.uploadFileSuccessEvent,
        UploadActions.createTextDocumentSuccessEvent
      ),
      concatMap(async () => {
        // Close the modal immediately
        await this.modalService.dismiss();
        // Return action to reset state
        return UploadActions.resetUploadStateCommand();
      })
    )
  );
}
