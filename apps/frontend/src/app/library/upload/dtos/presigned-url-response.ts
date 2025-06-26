/**
 * Presigned URL response DTO
 * Contains the upload URL and related data
 */
export interface PresignedUrlResponseDto {
  upload_id: string;
  document_id: string;
  upload_url: string;
  fields: Record<string, string>;
  expires_at: string;
}
