/**
 * Restore document request DTO
 * Request body for restoring archived documents
 */
export interface RestoreDocumentRequestDto {
  document_ids: string[];
  folder_id: string | null;
}
