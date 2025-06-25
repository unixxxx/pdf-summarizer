// Domain models for upload functionality

export interface UploadResult {
  documentId: string;
  fileName: string;
  fileSize: number;
  uploadedAt: string;
}

export interface UploadProgress {
  fileId: string;
  fileName: string;
  progress: number;
  stage?: string;
}

export interface UploadEvent {
  type: 'start' | 'progress' | 'success' | 'error' | 'cancel';
  fileId?: string;
  fileName?: string;
  progress?: number;
  stage?: string;
  error?: string;
  result?: UploadResult;
}

export type UploadMethod = 'presigned_post' | 'presigned_url';

export interface PresignedUrlRequest {
  filename: string;
  file_size: number;
  content_type: string;
  file_hash: string;
  folder_id?: string;
  upload_method?: UploadMethod;
}

export interface PresignedUrlResponse {
  upload_url: string;
  upload_id: string;
  document_id: string;
  fields: Record<string, string>;
  expires_at: string;
  method: UploadMethod;
  // For multipart uploads
  bucket?: string;
  key?: string;
  credentials?: {
    region: string;
    endpoint?: string;
  };
}

export interface CreateTextDocumentRequest {
  title: string;
  content: string;
  folder_id?: string;
}

export type UploadType = 'file' | 'text';
