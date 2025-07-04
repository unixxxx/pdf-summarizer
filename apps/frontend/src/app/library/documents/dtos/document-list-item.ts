import { TagDto } from '../../tag/dtos/tag';
import { DocumentStatus } from './document-status';

/**
 * Document list item DTO matching backend DocumentListItemResponse
 * Used for document listing/browsing
 */
export interface DocumentListItemDto {
  id: string; // Document ID
  document_id: string;
  filename: string;
  file_size: number;
  summary: string; // First 200 chars of extracted_text
  word_count: number;
  created_at: string;
  tags: TagDto[];
  status: DocumentStatus;
  folder_id?: string;
  error_message?: string | null; // Error message if processing failed
}
