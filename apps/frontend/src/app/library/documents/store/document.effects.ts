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
import { WebSocketService } from '../../../core/services/websocket.service';
import { DocumentProcessingEvent } from '../dtos/websocket-events';

@Injectable()
export class DocumentEffects {
  private actions$ = inject(Actions);
  private store = inject(Store);
  private documentService = inject(DocumentService);
  private uiStore = inject(UIStore);
  private modalService = inject(ModalService);
  private webSocketService = inject(WebSocketService);

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

  // Retry document processing
  retryDocumentProcessing$ = createEffect(() =>
    this.actions$.pipe(
      ofType(DocumentActions.retryDocumentProcessingCommand),
      switchMap(({ documentId }) =>
        this.documentService.retryProcessing(documentId).pipe(
          map((response) => {
            this.uiStore.showSuccess('Document processing retry queued');
            return DocumentActions.retryDocumentProcessingSuccessEvent({
              documentId,
              jobId: response.job_id,
            });
          }),
          catchError((error) => {
            this.uiStore.showError(error.message || 'Failed to retry processing');
            return of(
              DocumentActions.retryDocumentProcessingFailureEvent({
                error: error.message || 'Failed to retry processing',
              })
            );
          })
        )
      )
    )
  );

  // Listen to WebSocket document processing updates
  listenToDocumentProcessing$ = createEffect(() =>
    this.webSocketService.messages$.pipe(
      filter((msg): msg is DocumentProcessingEvent => msg.type === 'document_processing'),
      map((event) => {
        // Check if it's an error event
        if (event.error || event.stage === 'failed') {
          return DocumentActions.documentProcessingFailureEvent({
            documentId: event.document_id,
            error: event.error || event.message || 'Processing failed',
          });
        }
        
        // Calculate overall progress based on stage and progress
        let overallProgress = 0;
        const rawProgress = event.progress; // 0-1 from backend
        
        // Map stages to overall progress ranges
        // First task (process_document): 0-30%
        // Second task (generate_document_embeddings): 30-70%
        // Third task (generate_document_summary): 70-100%
        switch (event.stage) {
          case 'downloading':
            if (event.message?.includes('summary generation')) {
              // In summary phase
              overallProgress = 70 + Math.round(rawProgress * 5); // 70-75%
            } else if (event.message?.includes('embedding generation')) {
              // In embedding phase
              overallProgress = 30 + Math.round(rawProgress * 5); // 30-35%
            } else {
              // In text extraction phase
              overallProgress = Math.round(rawProgress * 15); // 0-15%
            }
            break;
          case 'extracting':
            if (event.message?.includes('summary') || event.message?.includes('language model')) {
              // Summary generation
              overallProgress = 75 + Math.round(rawProgress * 15); // 75-90%
            } else {
              // Text extraction
              overallProgress = 15 + Math.round(rawProgress * 15); // 15-30%
            }
            break;
          case 'chunking':
            overallProgress = 35 + Math.round(rawProgress * 5); // 35-40%
            break;
          case 'embedding':
            overallProgress = 40 + Math.round(rawProgress * 25); // 40-65%
            break;
          case 'storing':
            if (event.message?.includes('summary')) {
              overallProgress = 90 + Math.round(rawProgress * 10); // 90-100%
            } else if (event.message?.includes('embedding')) {
              overallProgress = 65 + Math.round(rawProgress * 5); // 65-70%
            } else {
              overallProgress = 25 + Math.round(rawProgress * 5); // 25-30%
            }
            break;
          case 'completed':
            overallProgress = 100;
            break;
          default:
            // Fallback to simple conversion
            overallProgress = Math.round(rawProgress * 100);
        }
        
        // Check if processing is complete
        if (event.stage === 'completed' || overallProgress >= 100) {
          // Extract document data from event
          if (event.document) {
            // Convert DTO to DocumentListItem
            const document = toDocumentListItem(event.document);
            return DocumentActions.documentProcessingCompleteEvent({
              document,
            });
          }
          
          // If completed but no document data, log error and treat as failure
          console.error('Document processing completed but no document data received', event);
          return DocumentActions.documentProcessingFailureEvent({
            documentId: event.document_id,
            error: 'Processing completed but document data is missing',
          });
        }

        // Otherwise it's a progress update
        return DocumentActions.documentProcessingUpdateEvent({
          documentId: event.document_id,
          stage: event.stage,
          progress: Math.min(99, overallProgress), // Cap at 99 until truly complete
          message: event.message,
        });
      })
    )
  );
}
