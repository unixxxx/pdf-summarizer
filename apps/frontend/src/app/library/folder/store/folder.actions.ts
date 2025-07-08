import { createActionGroup, emptyProps, props } from '@ngrx/store';
import { FolderTreeDto } from '../dtos/folder-tree';
import { FolderItemDto } from '../dtos/folder-item';
import { FolderCreateDto } from '../dtos/folder-create';
import { FolderUpdateDto } from '../dtos/folder-update';
import { FolderItem } from './state/folder-item';

export const FolderActions = createActionGroup({
  source: 'Folder',
  events: {
    // Folder fetch operations
    'Fetch folders command': emptyProps(),
    'Fetch folders success event': props<{ folder: FolderTreeDto }>(),
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

    // Document operations
    'Add documents to folder command': props<{
      from: string | undefined;
      to: string;
      documentId: string;
    }>(),
    'Add documents to folder success event': props<{
      from: string | undefined;
      to: string;
      documentId: string;
    }>(),
    'Add documents to folder failure event': props<{ error: string }>(),
    
    // Move document to unfiled
    'Move document to unfiled command': props<{
      documentId: string;
      from: string;
    }>(),
    'Move document to unfiled success event': props<{
      documentId: string;
      from: string;
    }>(),
    'Move document to unfiled failure event': props<{ error: string }>(),
    
    // Bulk update folder counts
    'Update folder counts after organization': props<{
      folderUpdates: Array<{ folderId: string; incrementBy: number }>;
    }>(),
  },
});
