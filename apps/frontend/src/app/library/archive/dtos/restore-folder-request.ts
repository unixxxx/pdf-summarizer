/**
 * Restore folder request DTO
 * Request body for restoring an archived folder
 */
export interface RestoreFolderRequestDto {
  folder_id: string;
  restore_children: boolean;
  new_parent_id: string | null;
}
