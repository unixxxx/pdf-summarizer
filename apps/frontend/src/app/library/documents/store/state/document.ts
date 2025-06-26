import { ToCamelCase } from '../../../../core/utils/transform';
import { DocumentListItemDto } from '../../dtos/document-list-item';
import { DocumentDetailDto } from '../../dtos/document-detail';
import { DocumentsListDto } from '../../dtos/documents-list-response';
import { Tag, toTag } from '../../../tag/store/state/tag';

/**
 * Document list item interface for the store
 * Represents a document in lists/tables
 */
export type DocumentListItem = Omit<
  ToCamelCase<DocumentListItemDto>,
  'tags'
> & {
  tags: Tag[];
};

/**
 * Document detail interface for the store
 * Represents a full document with all its data
 */
export type DocumentDetail = Omit<ToCamelCase<DocumentDetailDto>, 'tags'> & {
  tags: Tag[];
};

/**
 * Documents list interface for the store
 * Represents paginated document list response
 */
export type DocumentsList = Omit<ToCamelCase<DocumentsListDto>, 'items'> & {
  items: DocumentListItem[];
};

/**
 * Convert DocumentListItemDto to DocumentListItem
 */
export const toDocumentListItem = (
  dto: DocumentListItemDto
): DocumentListItem => ({
  id: dto.id,
  documentId: dto.document_id,
  filename: dto.filename,
  fileSize: dto.file_size,
  summary: dto.summary,
  wordCount: dto.word_count,
  createdAt: dto.created_at,
  tags: dto.tags.map(toTag),
  status: dto.status,
  folderId: dto.folder_id,
});

/**
 * Convert DocumentDetailDto to DocumentDetail
 */
export const toDocumentDetail = (dto: DocumentDetailDto): DocumentDetail => ({
  id: dto.id,
  filename: dto.filename,
  fileSize: dto.file_size,
  fileHash: dto.file_hash,
  extractedText: dto.extracted_text,
  wordCount: dto.word_count,
  createdAt: dto.created_at,
  status: dto.status,
  storagePath: dto.storage_path,
  folderId: dto.folder_id,
  tags: [],
});

/**
 * Convert DocumentsListDto to DocumentsList
 */
export const toDocumentsList = (dto: DocumentsListDto): DocumentsList => ({
  items: dto.items.map(toDocumentListItem),
  total: dto.total,
  limit: dto.limit,
  offset: dto.offset,
  hasMore: dto.has_more,
});
