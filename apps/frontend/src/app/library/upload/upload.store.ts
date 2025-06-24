import { computed, inject } from '@angular/core';
import {
  signalStore,
  withState,
  withComputed,
  withMethods,
  patchState,
} from '@ngrx/signals';
import { rxMethod } from '@ngrx/signals/rxjs-interop';
import { pipe, switchMap, tap, catchError, of } from 'rxjs';
import { tapResponse } from '@ngrx/operators';
import { UploadService } from './upload.service';
import {
  UploadEvent,
  UploadState,
  CreateTextDocumentRequest,
} from './upload.model';
const initialState: UploadState = {
  isUploading: false,
  uploadProgress: 0,
  currentFileName: null,
  currentStage: null,
  error: null,
};

export const UploadStore = signalStore(
  { providedIn: 'root' },
  withState(initialState),
  withComputed((store) => ({
    uploadStatus: computed(() => {
      if (store.error()) return 'error';
      if (store.isUploading()) return 'uploading';
      return 'idle';
    }),
  })),
  withMethods((store) => {
    const uploadService = inject(UploadService);

    return {
      uploadFile: rxMethod<{ file: File; folderId?: string }>(
        pipe(
          tap(() =>
            patchState(store, {
              isUploading: true,
              uploadProgress: 0,
              currentStage: null,
              error: null,
            })
          ),
          switchMap(({ file, folderId }) =>
            uploadService.uploadFile(file, folderId).pipe(
              tap((event: UploadEvent) => {
                switch (event.type) {
                  case 'start':
                    patchState(store, {
                      currentFileName: event.fileName,
                      uploadProgress: 0,
                    });
                    break;
                  case 'progress':
                    patchState(store, {
                      uploadProgress: event.progress || 0,
                    });
                    break;
                  case 'success':
                    patchState(store, {
                      isUploading: false,
                      uploadProgress: 100,
                      currentFileName: event.fileName,
                      error: null,
                    });
                    break;
                  case 'error':
                    patchState(store, {
                      isUploading: false,
                      uploadProgress: 0,
                      error: event.error || 'Upload failed',
                      currentFileName: null,
                    });
                    break;
                }
              }),
              catchError((error) => {
                patchState(store, {
                  isUploading: false,
                  uploadProgress: 0,
                  error: error.message || 'Upload failed',
                  currentFileName: null,
                });
                return of(null);
              })
            )
          )
        )
      ),

      createTextDocument: rxMethod<CreateTextDocumentRequest>(
        pipe(
          tap(() =>
            patchState(store, {
              isUploading: true,
              error: null,
            })
          ),
          switchMap((document) =>
            uploadService.createTextDocument(document).pipe(
              tapResponse({
                next: (event) => {
                  if (event.type === 'success') {
                    patchState(store, {
                      isUploading: false,
                      error: null,
                    });
                  }
                },
                error: (error: Error) => {
                  patchState(store, {
                    isUploading: false,
                    error: error.message || 'Failed to create document',
                  });
                },
              })
            )
          )
        )
      ),

      reset: () => patchState(store, initialState),
    };
  })
);
