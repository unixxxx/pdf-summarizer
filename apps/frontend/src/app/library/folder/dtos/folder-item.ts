import { TagDto } from '../../tag/dtos/tag';

/**
 * Folder item DTO
 * Represents a single folder in the hierarchy
 */
export interface FolderItemDto {
  id: string;
  name: string;
  description: string | undefined;
  color: string;
  parent_id: string | undefined;
  tags: TagDto[];
  created_at: string;
  updated_at: string;
  document_count: number;
  children_count: number;
  children: FolderItemDto[] | undefined;
}
