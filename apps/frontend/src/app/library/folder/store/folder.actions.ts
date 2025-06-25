import { createActionGroup, emptyProps, props } from '@ngrx/store';
import {
  FolderCreateDto,
  FolderDto,
  FolderItemDto,
  FolderUpdateDto,
} from '../dtos/folder';
import { FolderItem } from './state/folder';

export const FolderActions = createActionGroup({
  source: 'Folder',
  events: {
    // Folder fetch operations
    'Fetch folders command': emptyProps(),
    'Fetch folders success event': props<{ folder: FolderDto }>(),
    'Fetch folders failure event': props<{ error: string }>(),

    // Folder CRUD operations
    'Create folder command': props<{ request: FolderCreateDto }>(),
    'Create folder success event': props<{ folder: FolderItemDto }>(),
    'Create folder failure event': props<{ error: string }>(),

    'Update folder command': props<{ id: string; request: FolderUpdateDto }>(),
    'Update folder success event': props<{ folder: FolderItemDto }>(),
    'Update folder failure event': props<{ error: string }>(),

    'Delete folder command': props<{ id: string }>(),
    'Delete folder success event': props<{ id: string }>(),
    'Delete folder failure event': props<{ error: string }>(),

    // Folder UI state
    'Select folder command': props<{ folderId: string | undefined }>(),
    'Toggle folder expanded command': props<{ folderId: string }>(),
    'Set drag over folder command': props<{ folderId: string | undefined }>(),

    // Folder modal actions
    'Open create folder modal command': props<{ parentId?: string }>(),
    'Open edit folder modal command': props<{ folder: FolderItem }>(),
    'Open delete folder modal command': props<{ folder: FolderItem }>(),
  },
});
