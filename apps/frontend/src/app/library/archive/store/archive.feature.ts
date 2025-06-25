import { createFeature, createSelector } from '@ngrx/store';
import { archiveReducer } from './archive.reducer';
import {
  AsyncDataItemState,
  unwrapAsyncDataItem,
} from '../../../core/utils/async-data-item';

export const archiveFeature = createFeature({
  name: 'archive',
  reducer: archiveReducer,
  extraSelectors: ({ selectArchive }) => ({
    selectArchiveStats: createSelector(selectArchive, (asyncArchive) => {
      if (asyncArchive.state !== AsyncDataItemState.LOADED) {
        return null;
      }
      return unwrapAsyncDataItem(asyncArchive).stats;
    }),
    selectArchivedFolders: createSelector(selectArchive, (asyncArchive) => {
      if (asyncArchive.state !== AsyncDataItemState.LOADED) {
        return [];
      }
      return unwrapAsyncDataItem(asyncArchive).folders;
    }),
    selectArchivedDocuments: createSelector(selectArchive, (asyncArchive) => {
      if (asyncArchive.state !== AsyncDataItemState.LOADED) {
        return [];
      }
      return unwrapAsyncDataItem(asyncArchive).documents;
    }),
    selectRootDocuments: createSelector(selectArchive, (asyncArchive) => {
      if (asyncArchive.state !== AsyncDataItemState.LOADED) {
        return [];
      }
      const data = unwrapAsyncDataItem(asyncArchive);
      const folderDocs = new Set<string>();

      // Collect all document IDs that are in folders
      const collectFolderDocIds = (folders: typeof data.folders) => {
        folders.forEach((folder) => {
          folder.documents?.forEach((doc) => folderDocs.add(doc.id));
          if (folder.children?.length > 0) {
            collectFolderDocIds(folder.children);
          }
        });
      };

      collectFolderDocIds(data.folders);

      // Return only documents not in any folder
      return data.documents.filter((doc) => !folderDocs.has(doc.id));
    }),
    selectIsArchiveEmpty: createSelector(selectArchive, (asyncArchive) => {
      if (asyncArchive.state !== AsyncDataItemState.LOADED) {
        return true;
      }
      const data = unwrapAsyncDataItem(asyncArchive);
      return data.folders.length === 0 && data.documents.length === 0;
    }),
    selectHasArchiveContent: createSelector(selectArchive, (asyncArchive) => {
      if (asyncArchive.state !== AsyncDataItemState.LOADED) {
        return false;
      }
      const data = unwrapAsyncDataItem(asyncArchive);
      return data.folders.length > 0 || data.documents.length > 0;
    }),
    selectCanEmptyArchive: createSelector(selectArchive, (asyncArchive) => {
      if (asyncArchive.state !== AsyncDataItemState.LOADED) {
        return false;
      }
      const data = unwrapAsyncDataItem(asyncArchive);
      return data.stats.totalDocuments > 0 || data.stats.totalFolders > 0;
    }),
  }),
});
