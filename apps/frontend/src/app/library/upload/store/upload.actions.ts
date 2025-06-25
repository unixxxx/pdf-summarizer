import { createActionGroup, emptyProps, props } from '@ngrx/store';
import { UploadResult, UploadProgress } from './state/upload';

export const UploadActions = createActionGroup({
  source: 'Upload',
  events: {
    // File upload operations
    'Upload file command': props<{ file: File }>(),
    'Upload file started event': props<{ fileId: string; fileName: string }>(),
    'Upload file progress event': props<{ progress: UploadProgress }>(),
    'Upload file success event': props<{ result: UploadResult }>(),
    'Upload file failure event': props<{ error: string; fileName: string }>(),

    // Text document operations
    'Create text document command': props<{
      title: string;
      content: string;
    }>(),
    'Create text document started event': props<{ fileName: string }>(),
    'Create text document success event': props<{ result: UploadResult }>(),
    'Create text document failure event': props<{
      error: string;
      fileName: string;
    }>(),

    // UI state operations
    'Reset upload state command': emptyProps(),
    
    // Upload dialog operations
    'Open upload dialog command': emptyProps(),
  },
});
