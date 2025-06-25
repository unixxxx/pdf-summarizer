import { ToCamelCase } from '../../../../core/utils/transform';
import {
  PresignedUrlRequestDto,
  PresignedUrlResponseDto,
  CreateTextDocumentRequestDto,
} from '../../dtos/upload';

// Component interfaces for upload functionality

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

export type UploadType = 'file' | 'text';

// Type aliases for cleaner code
export type PresignedUrlRequest = ToCamelCase<PresignedUrlRequestDto>;
export type PresignedUrlResponse = ToCamelCase<PresignedUrlResponseDto>;
export type CreateTextDocumentRequest =
  ToCamelCase<CreateTextDocumentRequestDto>;
