export interface UploadEvent {
  type: 'start' | 'progress' | 'success' | 'error' | 'cancel';
  fileId?: string;
  fileName?: string;
  progress?: number;
  error?: string;
  result?: UploadResult;
}

export interface UploadResult {
  documentId: string;
  fileName: string;
  fileSize: number;
  uploadedAt: string;
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

export interface TextDocument {
  title: string;
  content: string;
  tags?: string[];
}

export interface CreateTextDocumentRequest {
  title: string;
  content: string;
  folder_id?: string;
  tags?: string[];
}

export type UploadType = 'file' | 'text';

export interface UploadState {
  isUploading: boolean;
  uploadProgress: number;
  currentFileName: string | null;
  currentStage: string | null;
  error: string | null;
}
