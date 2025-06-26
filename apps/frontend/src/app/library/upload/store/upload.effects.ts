import { Injectable, inject } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { mergeMap, tap, concatMap } from 'rxjs/operators';
import { of, concat } from 'rxjs';
import { UploadActions } from './upload.actions';
import { UploadService } from '../services/upload.service';
import { ModalService } from '../../../core/services/modal';
import { UploadDialog } from '../components/upload-dialog';
import { concatLatestFrom, mapResponse } from '@ngrx/operators';
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
            mapResponse({
              next: (event) => {
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
                      folderId: folderId || null,
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
              },
              error: (error: {
                error?: { detail?: string };
                detail?: string;
                message?: string;
              }) => {
                // Extract error message from various possible formats
                let errorMessage = 'Upload failed';

                if (error.error?.detail) {
                  errorMessage = error.error.detail;
                } else if (error.detail) {
                  errorMessage = error.detail;
                } else if (error.message) {
                  errorMessage = error.message;
                }

                return UploadActions.uploadFileFailureEvent({
                  error: errorMessage,
                  fileName: file.name,
                });
              },
            })
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
              mapResponse({
                next: (event) => {
                  switch (event.type) {
                    case 'progress':
                      return UploadActions.uploadFileProgressEvent({
                        progress: {
                          fileId: event.fileId || crypto.randomUUID(),
                          fileName: event.fileName || title,
                          progress: event.progress || 0,
                          stage: event.stage,
                        },
                      });
                    case 'success':
                      if (!event.result) {
                        return UploadActions.createTextDocumentFailureEvent({
                          error: 'Document created but no result returned',
                          fileName: title,
                        });
                      }
                      return UploadActions.createTextDocumentSuccessEvent({
                        result: event.result,
                        folderId: folderId || null,
                      });
                    case 'error':
                      return UploadActions.createTextDocumentFailureEvent({
                        error: event.error || 'Failed to create document',
                        fileName: title,
                      });
                    default:
                      // Handle any other event types as progress
                      return UploadActions.uploadFileProgressEvent({
                        progress: {
                          fileId: event.fileId || crypto.randomUUID(),
                          fileName: event.fileName || title,
                          progress: 0,
                        },
                      });
                  }
                },
                error: (error: {
                  error?: { detail?: string };
                  detail?: string;
                  message?: string;
                }) => {
                  // Extract error message from various possible formats
                  let errorMessage = 'Failed to create document';

                  if (error.error?.detail) {
                    errorMessage = error.error.detail;
                  } else if (error.detail) {
                    errorMessage = error.detail;
                  } else if (error.message) {
                    errorMessage = error.message;
                  }

                  return UploadActions.createTextDocumentFailureEvent({
                    error: errorMessage,
                    fileName: title,
                  });
                },
              })
            )
        )
      )
    )
  );

  // Open upload dialog
  openUploadDialog$ = createEffect(() =>
    this.actions$.pipe(
      ofType(UploadActions.openUploadDialogCommand),
      concatMap(async () => {
        const modal = await this.modalService.create({
          component: UploadDialog,
          backdropDismiss: true,
          animated: true,
          cssClass: 'upload-modal',
        });

        // Wait for modal to be dismissed
        await modal.onDidDismiss();

        // Return reset action after modal is dismissed
        return UploadActions.resetUploadStateCommand();
      })
    )
  );

  // Handle successful upload - close modal and reset state
  handleUploadSuccess$ = createEffect(
    () =>
      this.actions$.pipe(
        ofType(
          UploadActions.uploadFileSuccessEvent,
          UploadActions.createTextDocumentSuccessEvent
        ),
        tap(async () => {
          // Close the modal immediately
          await this.modalService.dismiss();
        })
      ),
    { dispatch: false }
  );
}
