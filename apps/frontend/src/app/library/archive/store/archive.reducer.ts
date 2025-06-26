import { createReducer, on } from '@ngrx/store';
import { ArchiveState } from './state/archive-state';
import { ArchiveActions } from './archive.actions';
import {
  AsyncDataItemState,
  wrapAsAsyncDataItem,
} from '../../../core/utils/async-data-item';

const initialState: ArchiveState = {
  archive: wrapAsAsyncDataItem(
    {
      stats: {
        totalDocuments: 0,
        totalFolders: 0,
        totalSize: 0,
        oldestItemDate: null,
      },
      folders: [],
      documents: [],
    },
    AsyncDataItemState.IDLE
  ),
};

export const archiveReducer = createReducer<ArchiveState>(
  initialState,
  // Archive fetch operations
  on(ArchiveActions.fetchArchiveCommand, (state) => ({
    ...state,
    archive: wrapAsAsyncDataItem(
      state.archive.data,
      AsyncDataItemState.LOADING
    ),
  })),
  on(
    ArchiveActions.fetchArchiveSuccessEvent,
    (state, { stats, folders, documents }) => ({
      ...state,
      archive: wrapAsAsyncDataItem(
        { stats, folders, documents },
        AsyncDataItemState.LOADED
      ),
    })
  ),
  on(ArchiveActions.fetchArchiveFailureEvent, (state, { error }) => ({
    ...state,
    archive: wrapAsAsyncDataItem(
      state.archive.data,
      AsyncDataItemState.ERROR,
      error
    ),
  })),

  // Restore operations
  on(ArchiveActions.restoreFolderCommand, (state) => state),
  on(ArchiveActions.restoreFolderSuccessEvent, (state, { folderId }) => {
    const currentData = state.archive.data;
    const updatedFolders = currentData.folders.filter(
      (folder) => folder.id !== folderId
    );
    const updatedStats = {
      ...currentData.stats,
      totalFolders: currentData.stats.totalFolders - 1,
    };

    return {
      ...state,
      archive: wrapAsAsyncDataItem(
        {
          ...currentData,
          stats: updatedStats,
          folders: updatedFolders,
        },
        AsyncDataItemState.LOADED
      ),
    };
  }),
  on(ArchiveActions.restoreFolderFailureEvent, (state) => state),

  on(ArchiveActions.restoreDocumentCommand, (state) => state),
  on(ArchiveActions.restoreDocumentSuccessEvent, (state, { documentId }) => {
    const currentData = state.archive.data;
    const updatedDocuments = currentData.documents.filter(
      (doc) => doc.id !== documentId
    );
    const updatedStats = {
      ...currentData.stats,
      totalDocuments: currentData.stats.totalDocuments - 1,
    };

    return {
      ...state,
      archive: wrapAsAsyncDataItem(
        {
          ...currentData,
          stats: updatedStats,
          documents: updatedDocuments,
        },
        AsyncDataItemState.LOADED
      ),
    };
  }),
  on(ArchiveActions.restoreDocumentFailureEvent, (state) => state),

  // Delete operations
  on(ArchiveActions.deleteFolderPermanentlyCommand, (state) => state),
  on(
    ArchiveActions.deleteFolderPermanentlySuccessEvent,
    (state, { folderId }) => {
      const currentData = state.archive.data;
      const folderToDelete = currentData.folders.find(
        (folder) => folder.id === folderId
      );
      if (!folderToDelete) {
        return state;
      }

      const updatedFolders = currentData.folders.filter(
        (folder) => folder.id !== folderId
      );

      // Count all documents in the folder and its children
      const countDocuments = (folder: typeof folderToDelete): number => {
        let count = folder.documents.length;
        folder.children.forEach((child) => {
          count += countDocuments(child);
        });
        return count;
      };

      const deletedDocumentCount = countDocuments(folderToDelete);
      const deletedFolderCount = 1 + folderToDelete.childrenCount;

      const updatedStats = {
        ...currentData.stats,
        totalFolders: currentData.stats.totalFolders - deletedFolderCount,
        totalDocuments: currentData.stats.totalDocuments - deletedDocumentCount,
      };

      return {
        ...state,
        archive: wrapAsAsyncDataItem(
          {
            ...currentData,
            stats: updatedStats,
            folders: updatedFolders,
          },
          AsyncDataItemState.LOADED
        ),
      };
    }
  ),
  on(ArchiveActions.deleteFolderPermanentlyFailureEvent, (state) => state),

  on(ArchiveActions.deleteDocumentPermanentlyCommand, (state) => state),
  on(
    ArchiveActions.deleteDocumentPermanentlySuccessEvent,
    (state, { documentId }) => {
      const currentData = state.archive.data;
      const updatedDocuments = currentData.documents.filter(
        (doc) => doc.id !== documentId
      );
      const updatedStats = {
        ...currentData.stats,
        totalDocuments: currentData.stats.totalDocuments - 1,
      };

      return {
        ...state,
        archive: wrapAsAsyncDataItem(
          {
            ...currentData,
            stats: updatedStats,
            documents: updatedDocuments,
          },
          AsyncDataItemState.LOADED
        ),
      };
    }
  ),
  on(ArchiveActions.deleteDocumentPermanentlyFailureEvent, (state) => state),

  // Empty archive
  on(ArchiveActions.emptyArchiveSuccessEvent, (state) => ({
    ...state,
    archive: wrapAsAsyncDataItem(
      {
        stats: {
          totalDocuments: 0,
          totalFolders: 0,
          totalSize: 0,
          oldestItemDate: null,
        },
        folders: [],
        documents: [],
      },
      AsyncDataItemState.LOADED
    ),
  }))
);
