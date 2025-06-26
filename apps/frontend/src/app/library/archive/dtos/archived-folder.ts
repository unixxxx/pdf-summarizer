/**
 * Archived folder DTO
 * Represents a folder in the archive
 */
export interface ArchivedFolderDto {
  id: string;
  name: string;
  archived_at: string;
  user_id: string;
  description: string | null;
  color: string | null;
  parent_id: string | null;
  parent_name: string | null;
  document_count: number;
  children_count: number;
}
