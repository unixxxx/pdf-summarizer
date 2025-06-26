/**
 * Archived document DTO
 * Represents a document in the archive
 */
export interface ArchivedDocumentDto {
  id: string;
  name: string;
  archived_at: string;
  user_id: string;
  file_size: number;
  page_count: number | null;
  folder_id: string | null;
  folder_name: string | null;
}
