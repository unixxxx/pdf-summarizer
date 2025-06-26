/**
 * Upload progress interface for the store
 * Tracks upload progress and status
 */
export interface UploadProgress {
  fileId: string;
  fileName: string;
  progress: number;
  stage?: string;
}
