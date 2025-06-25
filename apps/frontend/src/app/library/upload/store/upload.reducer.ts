import { createReducer, on } from '@ngrx/store';
import { UploadActions } from './upload.actions';
import { UploadState } from './state/upload-state';
import { 
  AsyncDataItemState,
  wrapAsAsyncDataItem
} from '../../../core/utils/async-data-item';

const initialState: UploadState = {
  uploadProgress: 0,
  currentFileName: null,
  currentStage: null,
  currentUpload: wrapAsAsyncDataItem(null, AsyncDataItemState.IDLE),
};

export const uploadReducer = createReducer(
  initialState,
  
  // File upload operations
  on(UploadActions.uploadFileStartedEvent, (state, { fileName }) => ({
    ...state,
    uploadProgress: 0,
    currentFileName: fileName,
    currentStage: 'uploading',
    currentUpload: wrapAsAsyncDataItem(null, AsyncDataItemState.LOADING),
  })),
  
  on(UploadActions.uploadFileProgressEvent, (state, { progress }) => ({
    ...state,
    uploadProgress: progress.progress,
    currentStage: progress.stage || state.currentStage,
  })),
  
  on(UploadActions.uploadFileSuccessEvent, (state, { result }) => ({
    ...state,
    uploadProgress: 100,
    currentStage: 'completed',
    currentUpload: wrapAsAsyncDataItem(result, AsyncDataItemState.LOADED),
  })),
  
  on(UploadActions.uploadFileFailureEvent, (state, { error }) => ({
    ...state,
    uploadProgress: 0,
    currentStage: 'error',
    currentUpload: wrapAsAsyncDataItem(null, AsyncDataItemState.ERROR, error),
  })),

  // Text document operations
  on(UploadActions.createTextDocumentStartedEvent, (state, { fileName }) => ({
    ...state,
    uploadProgress: 0,
    currentFileName: fileName,
    currentStage: 'creating',
    currentUpload: wrapAsAsyncDataItem(null, AsyncDataItemState.LOADING),
  })),
  
  on(UploadActions.createTextDocumentSuccessEvent, (state, { result }) => ({
    ...state,
    uploadProgress: 100,
    currentStage: 'completed',
    currentUpload: wrapAsAsyncDataItem(result, AsyncDataItemState.LOADED),
  })),
  
  on(UploadActions.createTextDocumentFailureEvent, (state, { error }) => ({
    ...state,
    uploadProgress: 0,
    currentStage: 'error',
    currentUpload: wrapAsAsyncDataItem(null, AsyncDataItemState.ERROR, error),
  })),

  // UI state operations
  on(UploadActions.resetUploadStateCommand, () => initialState),
);