/**
 * Complete upload request DTO
 * Used to notify the backend that upload is complete
 */
export interface CompleteUploadRequestDto {
  upload_id: string;
  document_id: string;
  key: string;
  filename: string;
  file_size: number;
  folder_id?: string;
}
