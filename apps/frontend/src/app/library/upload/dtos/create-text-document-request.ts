/**
 * Create text document request DTO
 * Used to create a text document from content
 */
export interface CreateTextDocumentRequestDto {
  title: string;
  content: string;
  folder_id?: string;
}
