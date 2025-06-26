/**
 * Presigned URL request DTO
 * Used to request a presigned URL for file upload
 */
export interface PresignedUrlRequestDto {
  filename: string;
  file_size: number;
  content_type: string;
  file_hash: string;
  folder_id?: string;
}
