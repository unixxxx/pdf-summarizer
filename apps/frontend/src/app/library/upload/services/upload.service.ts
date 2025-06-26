import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject, throwError, of } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';
import { UploadEvent } from '../store/state/upload-event';
import { PresignedUrlRequestDto } from '../dtos/presigned-url-request';
import { PresignedUrlResponseDto } from '../dtos/presigned-url-response';
import { CreateTextDocumentRequestDto } from '../dtos/create-text-document-request';
import { CompleteUploadRequestDto } from '../dtos/complete-upload-request';
import { CompleteUploadResponseDto } from '../dtos/complete-upload-response';

@Injectable({
  providedIn: 'root',
})
export class UploadService {
  private http = inject(HttpClient);
  private uploadEvents$ = new Subject<UploadEvent>();

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
    const maxFileSize = 500 * 1024 * 1024; // 500MB

    // Check file size before starting
    if (file.size > maxFileSize) {
      const errorEvent: UploadEvent = {
        type: 'error',
        fileId,
        fileName: file.name,
        error: `File size exceeds maximum allowed size of 500MB. Your file is ${Math.round(
          file.size / 1024 / 1024
        )}MB.`,
      };
      this.uploadEvents$.next(errorEvent);
      return throwError(() => new Error(errorEvent.error));
    }

    // Emit start event
    this.uploadEvents$.next({
      type: 'start',
      fileId,
      fileName: file.name,
    });

    // Calculate file hash first
    return new Observable<UploadEvent>((observer) => {
      this.calculateFileHash(file)
        .then((fileHash) => {
          let presignedData: PresignedUrlResponseDto;
          let uploadCompleted = false;

          // Get presigned POST URL
          const contentType =
            file.type ||
            (file.name.endsWith('.txt') ? 'text/plain' : 'application/pdf');

          this.getPresignedUrl({
            filename: file.name,
            file_size: file.size,
            content_type: contentType,
            file_hash: fileHash,
            folder_id: folderId,
          })
            .pipe(
              switchMap((data) => {
                presignedData = data;
                // Upload file using presigned POST
                return this.uploadUsingPresignedPost(
                  file,
                  presignedData.upload_url,
                  presignedData.fields,
                  fileId
                );
              }),
              switchMap((event) => {
                // Pass through progress events
                if (event.type === 'progress' && event.stage === 'uploading') {
                  return of(event);
                }

                // When upload is complete, call backend to finalize
                if (
                  event.type === 'progress' &&
                  event.stage === 'processing' &&
                  !uploadCompleted
                ) {
                  uploadCompleted = true;
                  return this.completeUpload({
                    upload_id: presignedData.upload_id,
                    document_id: presignedData.document_id,
                    key: presignedData.fields['key'],
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
              }),
              catchError((error) => {
                let errorMessage = 'Upload failed';

                // Check various error response formats
                if (error.error?.detail) {
                  // Standard API error response format
                  errorMessage = error.error.detail;
                } else if (error.detail) {
                  // Direct detail property
                  errorMessage = error.detail;
                } else if (error.error && typeof error.error === 'string') {
                  // Plain string error
                  errorMessage = error.error;
                } else if (error.message) {
                  // JavaScript error message
                  errorMessage = error.message;
                } else if (typeof error === 'string') {
                  // Plain string
                  errorMessage = error;
                }

                // Clean up error message if it contains HTTP status prefix
                const match = errorMessage.match(/^\d+:\s*(.+)$/);
                if (match) {
                  errorMessage = match[1];
                }

                // Remove "Failed to generate upload URL:" prefix if present
                if (errorMessage.startsWith('Failed to generate upload URL:')) {
                  errorMessage = errorMessage.replace(
                    /^Failed to generate upload URL:\s*\d*:\s*/,
                    ''
                  );
                }

                const errorEvent: UploadEvent = {
                  type: 'error',
                  fileId,
                  fileName: file.name,
                  error: errorMessage,
                };
                this.uploadEvents$.next(errorEvent);
                return throwError(() => error);
              })
            )
            .subscribe({
              next: (event) => {
                observer.next(event);
                this.uploadEvents$.next(event);
              },
              error: (error) => observer.error(error),
              complete: () => observer.complete(),
            });
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
    document: CreateTextDocumentRequestDto
  ): Observable<UploadEvent> {
    // Keep the original title with .txt extension for the filename
    // The backend will handle any necessary sanitization for storage
    const filename = `${document.title}.txt`;

    // Convert text content to a File object
    const blob = new Blob([document.content], { type: 'text/plain' });
    const file = new File([blob], filename, {
      type: 'text/plain',
      lastModified: Date.now(),
    });

    // Use the same upload flow as regular files
    return this.uploadFile(file, document.folder_id);
  }

  /**
   * Get presigned URL for file upload
   */
  private getPresignedUrl(
    request: PresignedUrlRequestDto
  ): Observable<PresignedUrlResponseDto> {
    return this.http.post<PresignedUrlResponseDto>(
      '/api/v1/upload/presigned-url',
      request
    );
  }

  /**
   * Upload file using presigned POST
   */
  private uploadUsingPresignedPost(
    file: File,
    uploadUrl: string,
    fields: Record<string, string>,
    fileId: string
  ): Observable<UploadEvent> {
    return new Observable<UploadEvent>((observer) => {
      const formData = new FormData();

      // Add all presigned fields to form data
      Object.entries(fields).forEach(([key, value]) => {
        formData.append(key, value);
      });

      // File must be added last
      formData.append('file', file);

      // Create XMLHttpRequest to track upload progress
      const xhr = new XMLHttpRequest();

      // Track upload progress
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const percentage = Math.round((event.loaded / event.total) * 100);
          observer.next({
            type: 'progress',
            fileId,
            fileName: file.name,
            progress: percentage,
            stage: 'uploading',
          });
        }
      });

      // Handle completion
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          // Emit final progress event
          observer.next({
            type: 'progress',
            fileId,
            fileName: file.name,
            progress: 100,
            stage: 'processing',
          });
          // Don't complete here - let the outer observable handle completion
        } else {
          observer.error(new Error(`Upload failed with status ${xhr.status}`));
        }
      });

      // Handle errors
      xhr.addEventListener('error', () => {
        observer.error(new Error('Upload failed'));
      });

      // Send the request
      xhr.open('POST', uploadUrl);
      xhr.send(formData);
    });
  }

  /**
   * Complete the upload process
   */
  private completeUpload(
    request: CompleteUploadRequestDto
  ): Observable<CompleteUploadResponseDto> {
    return this.http.post<CompleteUploadResponseDto>(
      '/api/v1/upload/complete',
      request
    );
  }
}
