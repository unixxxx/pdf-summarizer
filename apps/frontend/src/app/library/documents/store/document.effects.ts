import { Injectable, inject } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import {
  switchMap,
  map,
  catchError,
  filter,
  withLatestFrom,
  tap,
  concatMap,
} from 'rxjs/operators';
import { of, from } from 'rxjs';
import { DocumentActions } from './document.actions';
import { DocumentService } from '../services/document.service';
import { toDocumentListItem } from './state/document';
import { documentFeature } from './document.feature';
import { UIStore } from '../../../shared/ui.store';
import { ModalService } from '../../../core/services/modal';
import { ConfirmDialog } from '../../../shared/components/confirm-dialog';

@Injectable()
export class DocumentEffects {
  private actions$ = inject(Actions);
  private store = inject(Store);
  private documentService = inject(DocumentService);
  private uiStore = inject(UIStore);
  private modalService = inject(ModalService);

  loadDocuments$ = createEffect(() =>
    this.actions$.pipe(
      ofType(DocumentActions.fetchDocumentsCommand),
      switchMap(({ criteria }) =>
        this.documentService.browse(criteria).pipe(
          map((response) =>
            DocumentActions.fetchDocumentsSuccessEvent({
              documents: response.items.map(toDocumentListItem),
              total: response.total,
              hasMore: response.has_more,
              offset: response.offset,
            })
          ),
          catchError((error) =>
            of(
              DocumentActions.fetchDocumentsFailureEvent({
                error: error.message || 'Failed to load documents',
              })
            )
          )
        )
      )
    )
  );

  loadMoreDocuments$ = createEffect(() =>
    this.actions$.pipe(
      ofType(DocumentActions.fetchMoreDocumentsCommand),
      withLatestFrom(this.store.select(documentFeature.selectPagination)),
      filter(([, pagination]) => pagination.hasMore),
      switchMap(([{ criteria }, pagination]) => {
        const newOffset = pagination.offset + pagination.limit;
        const searchCriteria = {
          ...criteria,
          limit: pagination.limit,
          offset: newOffset,
        };
        return this.documentService.browse(searchCriteria).pipe(
          map((response) =>
            DocumentActions.fetchMoreDocumentsSuccessEvent({
              documents: response.items.map(toDocumentListItem),
              total: response.total,
              hasMore: response.has_more,
              offset: response.offset,
            })
          ),
          catchError((error) =>
            of(
              DocumentActions.fetchMoreDocumentsFailureEvent({
                error: error.message || 'Failed to load more documents',
              })
            )
          )
        );
      })
    )
  );

  deleteDocument$ = createEffect(() =>
    this.actions$.pipe(
      ofType(DocumentActions.deleteDocumentCommand),
      withLatestFrom(this.store.select(documentFeature.selectDocuments)),
      concatMap(([{ documentId }, documents]) => {
        // Find the document to get its folder ID before deletion
        const document = documents.data?.find(
          (doc) => doc.documentId === documentId
        );
        const folderId = document?.folderId;

        return this.documentService.delete(documentId).pipe(
          map(() => {
            this.uiStore.showSuccess('Document moved to archive');
            return DocumentActions.deleteDocumentSuccessEvent({
              documentId,
              folderId,
            });
          }),
          catchError((error) => {
            this.uiStore.showError('Failed to delete document');
            return of(
              DocumentActions.deleteDocumentFailureEvent({
                error: error.message || 'Failed to delete document',
              })
            );
          })
        );
      })
    )
  );

  exportDocument$ = createEffect(
    () =>
      this.actions$.pipe(
        ofType(DocumentActions.exportDocumentCommand),
        tap(({ documentId, format, filename }) => {
          this.documentService.exportDocument(documentId, format).subscribe({
            next: (blob) => {
              const url = window.URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `${filename}.${format}`;
              document.body.appendChild(a);
              a.click();
              window.URL.revokeObjectURL(url);
              document.body.removeChild(a);

              this.store.dispatch(
                DocumentActions.exportDocumentSuccessEvent({
                  documentId,
                  format,
                })
              );
            },
            error: (error) => {
              this.uiStore.showError('Failed to export document');
              this.store.dispatch(
                DocumentActions.exportDocumentFailureEvent({
                  error: error.message || 'Failed to export document',
                })
              );
            },
          });
        })
      ),
    { dispatch: false }
  );

  downloadDocument$ = createEffect(
    () =>
      this.actions$.pipe(
        ofType(DocumentActions.downloadDocumentCommand),
        tap(({ documentId, filename }) => {
          this.documentService.download(documentId).subscribe({
            next: (blob) => {
              const url = window.URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = filename;
              document.body.appendChild(a);
              a.click();
              window.URL.revokeObjectURL(url);
              document.body.removeChild(a);

              this.store.dispatch(
                DocumentActions.downloadDocumentSuccessEvent({ documentId })
              );
            },
            error: (error) => {
              this.uiStore.showError('Failed to download document');
              this.store.dispatch(
                DocumentActions.downloadDocumentFailureEvent({
                  error: error.message || 'Failed to download document',
                })
              );
            },
          });
        })
      ),
    { dispatch: false }
  );

  // Handle delete document modal
  openDeleteDocumentModal$ = createEffect(() =>
    this.actions$.pipe(
      ofType(DocumentActions.openDeleteDocumentModalCommand),
      switchMap(({ document }) => {
        const message = `Are you sure you want to move "${document.filename}" to the archive? You can restore it later if needed.`;

        return from(
          this.modalService.create<boolean>({
            component: ConfirmDialog,
            inputs: {
              title: 'Move Document to Archive',
              message,
              confirmText: 'Move to Archive',
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
                  return DocumentActions.deleteDocumentCommand({
                    documentId: document.id,
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
}
