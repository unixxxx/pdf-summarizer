/**
 * Archive statistics DTO
 * Provides summary information about archived items
 */
export interface ArchiveStatsDto {
  total_documents: number;
  total_folders: number;
  total_size: number;
  oldest_item_date: string | null;
}
