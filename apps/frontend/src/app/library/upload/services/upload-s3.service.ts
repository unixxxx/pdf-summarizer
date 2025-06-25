import { Injectable } from '@angular/core';
import { S3Client } from '@aws-sdk/client-s3';
import { Upload } from '@aws-sdk/lib-storage';
import { Observable } from 'rxjs';
import { UploadEvent } from '../store/state/upload';

export interface S3UploadConfig {
  region: string;
  credentials?: {
    accessKeyId: string;
    secretAccessKey: string;
    sessionToken?: string;
  };
  endpoint?: string;
}

@Injectable({
  providedIn: 'root',
})
export class S3UploadService {
  private s3Client: S3Client | null = null;

  /**
   * Initialize S3 client with temporary credentials
   */
  initializeClient(config: S3UploadConfig): void {
    this.s3Client = new S3Client({
      region: config.region,
      credentials: config.credentials,
      endpoint: config.endpoint,
    });
  }

  /**
   * Upload file to S3 using multipart upload
   */
  uploadToS3(
    file: File,
    bucket: string,
    key: string,
    fileId: string,
    metadata?: Record<string, string>
  ): Observable<UploadEvent> {
    return new Observable<UploadEvent>((observer) => {
      if (!this.s3Client) {
        observer.error(new Error('S3 client not initialized'));
        return;
      }

      // Create multipart upload
      const upload = new Upload({
        client: this.s3Client,
        params: {
          Bucket: bucket,
          Key: key,
          Body: file,
          ContentType: file.type || 'application/octet-stream',
          Metadata: metadata,
        },
        queueSize: 4, // Concurrent parts
        partSize: 5 * 1024 * 1024, // 5MB parts
        leavePartsOnError: false,
      });

      // Track progress
      upload.on('httpUploadProgress', (progress) => {
        if (progress.loaded && progress.total) {
          const percentage = Math.round(
            (progress.loaded / progress.total) * 100
          );
          observer.next({
            type: 'progress',
            fileId,
            fileName: file.name,
            progress: percentage,
          });
        }
      });

      // Start upload
      upload
        .done()
        .then(() => {
          observer.next({
            type: 'success',
            fileId,
            fileName: file.name,
            result: {
              documentId: fileId,
              fileName: file.name,
              fileSize: file.size,
              uploadedAt: new Date().toISOString(),
            },
          });
          observer.complete();
        })
        .catch((error) => {
          observer.error(error);
        });

      // Return abort function for cancellation
      return () => {
        upload.abort();
      };
    });
  }

  /**
   * Upload using presigned POST (for smaller files)
   */
  uploadWithPresignedPost(
    file: File,
    url: string,
    fields: Record<string, string>,
    fileId: string
  ): Observable<UploadEvent> {
    return new Observable<UploadEvent>((observer) => {
      const formData = new FormData();

      // Add all fields from presigned response
      Object.entries(fields).forEach(([key, value]) => {
        formData.append(key, value);
      });

      // File must be last
      formData.append('file', file);

      // Use fetch API to avoid CORS preflight
      const xhr = new XMLHttpRequest();

      // Track upload progress
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const progress = Math.round((100 * event.loaded) / event.total);
          observer.next({
            type: 'progress',
            fileId,
            fileName: file.name,
            progress,
          });
        }
      });

      // Handle successful upload
      xhr.addEventListener('load', () => {
        if (xhr.status === 204 || xhr.status === 200 || xhr.status === 201) {
          observer.next({
            type: 'success',
            fileId,
            fileName: file.name,
            result: {
              documentId: fileId,
              fileName: file.name,
              fileSize: file.size,
              uploadedAt: new Date().toISOString(),
            },
          });
          observer.complete();
        } else {
          observer.error(new Error(`Upload failed with status ${xhr.status}`));
        }
      });

      // Handle upload errors
      xhr.addEventListener('error', () => {
        observer.error(new Error('Upload failed'));
      });

      // Open and send request
      xhr.open('POST', url);
      xhr.send(formData);

      // Return abort function
      return () => {
        xhr.abort();
      };
    });
  }
}
