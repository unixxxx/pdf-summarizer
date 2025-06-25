import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject, throwError, of } from 'rxjs';
import { catchError, map, switchMap, tap, mergeMap } from 'rxjs/operators';
import {
  UploadEvent,
  PresignedUrlRequest,
  PresignedUrlResponse,
  CreateTextDocumentRequest,
} from '../store/state/upload';
import { S3UploadService } from './upload-s3.service';
import { uploadConfig } from '../../../../environments/upload.config';

@Injectable({
  providedIn: 'root',
})
export class UploadService {
  private http = inject(HttpClient);
  private uploadEvents$ = new Subject<UploadEvent>();
  private s3Service = inject(S3UploadService);

  // Configuration from centralized config
  private config = uploadConfig;

  /**
   * Calculate SHA-256 hash of a file
   */
  private async calculateFileHash(file: File): Promise<string> {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');
    return hashHex;
  }

  /**
   * Upload a file using presigned URL
   */
  uploadFile(file: File, folderId?: string): Observable<UploadEvent> {
    const fileId = crypto.randomUUID();

    // Emit start event
    this.uploadEvents$.next({
      type: 'start',
      fileId,
      fileName: file.name,
    });

    // Determine upload method based on file size
    const useMultipart = file.size > this.config.multipartThreshold;

    // Calculate file hash first
    return new Observable<UploadEvent>((observer) => {
      this.calculateFileHash(file)
        .then((fileHash) => {
          // Direct S3 upload using presigned URL
          this.getPresignedUrl({
            filename: file.name,
            file_size: file.size,
            content_type: file.type || 'application/pdf',
            file_hash: fileHash,
            folder_id: folderId,
            upload_method: useMultipart ? 'presigned_url' : 'presigned_post',
          })
            .pipe(
              switchMap((presignedData) => {
                if (
                  presignedData.method === 'presigned_url' &&
                  presignedData.bucket &&
                  presignedData.key
                ) {
                  // Use multipart upload for large files
                  if (presignedData.credentials) {
                    this.s3Service.initializeClient({
                      region: presignedData.credentials.region,
                      endpoint: presignedData.credentials.endpoint,
                    });
                  }

                  const key = presignedData.key; // TypeScript now knows this is defined
                  return this.s3Service
                    .uploadToS3(file, presignedData.bucket, key, fileId)
                    .pipe(
                      mergeMap((event) => {
                        if (event.type === 'success') {
                          // Complete the upload in backend
                          return this.completeUpload({
                            upload_id: presignedData.upload_id,
                            document_id: presignedData.document_id,
                            key: key,
                            filename: file.name,
                            file_size: file.size,
                            folder_id: folderId,
                          }).pipe(
                            map((response) => ({
                              type: 'success' as const,
                              fileId,
                              fileName: file.name,
                              result: {
                                documentId: response.document_id,
                                fileName: file.name,
                                fileSize: file.size,
                                uploadedAt: new Date().toISOString(),
                              },
                            }))
                          );
                        }
                        return of(event);
                      })
                    );
                } else {
                  // Use presigned POST for smaller files
                  return this.s3Service
                    .uploadWithPresignedPost(
                      file,
                      presignedData.upload_url,
                      presignedData.fields,
                      fileId
                    )
                    .pipe(
                      mergeMap((event) => {
                        if (event.type === 'success') {
                          // Complete the upload in backend
                          return this.completeUpload({
                            upload_id: presignedData.upload_id,
                            document_id: presignedData.document_id,
                            key:
                              presignedData.fields['key'] ||
                              `uploads/${presignedData.upload_id}/${file.name}`,
                            filename: file.name,
                            file_size: file.size,
                            folder_id: folderId,
                          }).pipe(
                            map((response) => ({
                              type: 'success' as const,
                              fileId,
                              fileName: file.name,
                              result: {
                                documentId: response.document_id,
                                fileName: file.name,
                                fileSize: file.size,
                                uploadedAt: new Date().toISOString(),
                              },
                            }))
                          );
                        }
                        return of(event);
                      })
                    );
                }
              }),
              tap((event) => this.uploadEvents$.next(event)),
              catchError((error) => {
                const errorEvent: UploadEvent = {
                  type: 'error',
                  fileId,
                  fileName: file.name,
                  error: error.message || 'Upload failed',
                };
                this.uploadEvents$.next(errorEvent);
                return throwError(() => error);
              })
            )
            .subscribe(observer);
        })
        .catch((error) => {
          const errorEvent: UploadEvent = {
            type: 'error',
            fileId,
            fileName: file.name,
            error: 'Failed to calculate file hash',
          };
          this.uploadEvents$.next(errorEvent);
          observer.error(error);
        });
    });
  }

  /**
   * Create a text document
   */
  createTextDocument(
    document: CreateTextDocumentRequest
  ): Observable<UploadEvent> {
    const fileId = crypto.randomUUID();

    // Emit start event
    this.uploadEvents$.next({
      type: 'start',
      fileId,
      fileName: document.title,
    });

    return this.http
      .post<{ id: string }>('/api/v1/document/text', document)
      .pipe(
        map((response) => {
          const successEvent: UploadEvent = {
            type: 'success',
            fileId,
            fileName: document.title,
            result: {
              documentId: response.id,
              fileName: document.title,
              fileSize: new Blob([document.content]).size,
              uploadedAt: new Date().toISOString(),
            },
          };
          this.uploadEvents$.next(successEvent);
          return successEvent;
        }),
        catchError((error) => {
          const errorEvent: UploadEvent = {
            type: 'error',
            fileId,
            fileName: document.title,
            error: error.error?.detail || 'Failed to create document',
          };
          this.uploadEvents$.next(errorEvent);
          return throwError(() => error);
        })
      );
  }

  /**
   * Get presigned URL for file upload
   */
  private getPresignedUrl(
    request: PresignedUrlRequest
  ): Observable<PresignedUrlResponse> {
    return this.http.post<PresignedUrlResponse>(
      '/api/v1/upload/presigned-url',
      request
    );
  }

  /**
   * Complete the upload process
   */
  private completeUpload(request: {
    upload_id: string;
    document_id: string;
    key: string;
    filename: string;
    file_size: number;
    folder_id?: string;
  }): Observable<{ document_id: string }> {
    return this.http.post<{ document_id: string }>(
      '/api/v1/upload/complete',
      request
    );
  }

}
