import { createActionGroup, emptyProps, props } from '@ngrx/store';
import {
  ArchivedDocument,
  ArchivedFolderWithChildren,
  ArchiveStats,
} from './state/archive';

export const ArchiveActions = createActionGroup({
  source: 'Archive',
  events: {
    // Archive fetch operations
    'Fetch archive command': emptyProps(),
    'Fetch archive success event': props<{
      stats: ArchiveStats;
      folders: ArchivedFolderWithChildren[];
      documents: ArchivedDocument[];
    }>(),
    'Fetch archive failure event': props<{ error: string }>(),

    // Restore operations
    'Restore folder command': props<{
      folderId: string;
      restoreChildren: boolean;
      newParentId: string | null;
    }>(),
    'Restore folder success event': props<{ folderId: string }>(),
    'Restore folder failure event': props<{ error: string }>(),

    'Restore document command': props<{
      documentIds: string[];
      folderId: string | null;
    }>(),
    'Restore document success event': props<{ documentIds: string[] }>(),
    'Restore document failure event': props<{ error: string }>(),

    // Delete operations
    'Delete folder permanently command': props<{
      folderId: string;
      deleteChildren: boolean;
    }>(),
    'Delete folder permanently success event': props<{ folderId: string }>(),
    'Delete folder permanently failure event': props<{ error: string }>(),

    'Delete document permanently command': props<{ documentIds: string[] }>(),
    'Delete document permanently success event': props<{
      documentIds: string[];
    }>(),
    'Delete document permanently failure event': props<{ error: string }>(),

    // Empty archive
    'Empty archive command': emptyProps(),
    'Empty archive success event': emptyProps(),
    'Empty archive failure event': props<{ error: string }>(),

    // Modal actions
    'Open restore folder modal command': props<{
      folder: ArchivedFolderWithChildren;
    }>(),
    'Open restore document modal command': props<{
      document: ArchivedDocument;
    }>(),
    'Open delete folder modal command': props<{
      folder: ArchivedFolderWithChildren;
    }>(),
    'Open delete document modal command': props<{
      document: ArchivedDocument;
    }>(),
    'Open empty archive modal command': emptyProps(),
  },
});
