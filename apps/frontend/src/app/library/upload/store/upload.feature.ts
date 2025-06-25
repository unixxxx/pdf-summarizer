import { createFeature, createSelector } from '@ngrx/store';
import { uploadReducer } from './upload.reducer';
import { AsyncDataItemState } from '../../../core/utils/async-data-item';

export const uploadFeature = createFeature({
  name: 'upload',
  reducer: uploadReducer,
  extraSelectors: ({ selectCurrentUpload, selectUploadProgress, selectCurrentStage }) => ({
    selectIsUploading: createSelector(
      selectCurrentUpload,
      (upload) => upload.state === AsyncDataItemState.LOADING
    ),
    selectUploadError: createSelector(
      selectCurrentUpload,
      (upload) => upload.state === AsyncDataItemState.ERROR ? upload.error : null
    ),
    selectUploadStatus: createSelector(
      selectCurrentUpload,
      selectUploadProgress,
      selectCurrentStage,
      (upload, progress, stage) => {
        if (upload.state === AsyncDataItemState.ERROR) return 'error';
        if (upload.state === AsyncDataItemState.LOADING) return 'uploading';
        if (progress === 100 && stage === 'completed') return 'completed';
        return 'idle';
      }
    ),
  }),
});