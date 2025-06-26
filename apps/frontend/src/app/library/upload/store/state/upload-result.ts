/**
 * Upload result interface for the store
 * Represents a completed upload
 */
export interface UploadResult {
  documentId: string;
  fileName: string;
  fileSize: number;
  uploadedAt: string;
}
