import { AsyncDataItem } from '../../../../core/utils/async-data-item';
import { UploadResult } from './upload';

export interface UploadState {
  uploadProgress: number;
  currentFileName: string | null;
  currentStage: string | null;
  currentUpload: AsyncDataItem<UploadResult | null>;
}