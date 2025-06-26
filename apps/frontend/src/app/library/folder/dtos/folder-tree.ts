import { FolderItemDto } from './folder-item';

/**
 * Folder tree response DTO
 * Contains the entire folder hierarchy with metadata
 */
export interface FolderTreeDto {
  folders: FolderItemDto[];
  total_count: number;
  unfiled_count: number;
  total_document_count: number;
}
