import { UploadResult } from './upload-result';

/**
 * Upload event interface for the store
 * Represents various upload lifecycle events
 */
export interface UploadEvent {
  type: 'start' | 'progress' | 'success' | 'error' | 'cancel';
  fileId?: string;
  fileName?: string;
  progress?: number;
  stage?: string;
  error?: string;
  result?: UploadResult;
}
