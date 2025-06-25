// API DTOs for upload endpoints

export interface PresignedUrlRequestDto {
  filename: string;
  file_size: number;
  content_type: string;
  file_hash: string;
  folder_id?: string;
}

export interface PresignedUrlResponseDto {
  upload_id: string;
  document_id: string;
  upload_url: string;
  fields: Record<string, string>;
  expires_at: string;
}

export interface CreateTextDocumentRequestDto {
  title: string;
  content: string;
  folder_id?: string;
}


export interface CompleteUploadRequestDto {
  upload_id: string;
  document_id: string;
  key: string;
  filename: string;
  file_size: number;
  folder_id?: string;
}

export interface CompleteUploadResponseDto {
  document_id: string;
}
