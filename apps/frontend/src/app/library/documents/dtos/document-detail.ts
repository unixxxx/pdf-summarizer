import { DocumentStatus } from './document-status';

/**
 * Document detail DTO matching backend DocumentDetailResponse
 * Used for individual document details
 */
export interface DocumentDetailDto {
  id: string;
  filename: string;
  file_size: number;
  file_hash: string;
  status: DocumentStatus;
  created_at: string;
  storage_path?: string;
  extracted_text?: string;
  word_count?: number;
  folder_id?: string;
  error_message?: string | null;
}
