import { DocumentListItemDto } from './document-list-item';

/**
 * Paginated response for document items
 * Matches backend DocumentsListResponse
 */
export interface DocumentsListDto {
  items: DocumentListItemDto[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}
