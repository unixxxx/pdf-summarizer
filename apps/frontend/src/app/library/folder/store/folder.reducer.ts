import { createReducer, on } from '@ngrx/store';
import { FolderState } from './state/folder-state';
import { FolderActions } from './folder.actions';
import {
  AsyncDataItemState,
  wrapAsAsyncDataItem,
} from '../../../core/utils/async-data-item';
import { FolderItem, toFolderItem, toFolders } from './state/folder';

const initialState: FolderState = {
  folder: wrapAsAsyncDataItem(
    {
      totalCount: 0,
      unfiledCount: 0,
      totalDocumentCount: 0,
      folders: [],
    },
    AsyncDataItemState.IDLE
  ),
  selectedFolderId: undefined,
  expandedFolders: [],
  dragOverFolder: undefined,
};

export const folderReducer = createReducer<FolderState>(
  initialState,
  // Folder fetch operations
  on(FolderActions.fetchFoldersCommand, (state) => ({
    ...state,
    folder: wrapAsAsyncDataItem(state.folder.data, AsyncDataItemState.LOADING),
  })),
  on(FolderActions.fetchFoldersSuccessEvent, (state, { folder }) => ({
    ...state,
    folder: wrapAsAsyncDataItem(toFolders(folder), AsyncDataItemState.LOADED),
  })),
  on(FolderActions.fetchFoldersFailureEvent, (state, { error }) => ({
    ...state,
    folder: wrapAsAsyncDataItem(
      state.folder.data,
      AsyncDataItemState.ERROR,
      error
    ),
  })),

  // Folder CRUD operations
  on(FolderActions.createFolderSuccessEvent, (state, { folder }) => {
    const newFolderItem = toFolderItem(folder);
    const currentData = state.folder.data;

    // Add the new folder to the correct location in the tree
    const updatedFolders = addFolderToTree(
      currentData.folders,
      newFolderItem,
      folder.parent_id
    );

    return {
      ...state,
      folder: wrapAsAsyncDataItem(
        {
          ...currentData,
          totalCount: currentData.totalCount + 1,
          folders: updatedFolders,
        },
        AsyncDataItemState.LOADED
      ),
    };
  }),

  on(FolderActions.updateFolderSuccessEvent, (state, { folder }) => {
    const updatedFolderItem = toFolderItem(folder);
    const currentData = state.folder.data;

    // Check if parent changed
    const oldFolder = findFolderInTree(currentData.folders, folder.id);
    const parentChanged =
      oldFolder && oldFolder.parentId !== updatedFolderItem.parentId;

    let updatedFolders;
    if (parentChanged) {
      // If parent changed, we need to move the folder
      updatedFolders = moveFolderInTree(
        [...currentData.folders],
        updatedFolderItem
      );
    } else {
      // Otherwise just update in place
      updatedFolders = updateFolderInTree(
        [...currentData.folders],
        updatedFolderItem
      );
    }

    return {
      ...state,
      folder: wrapAsAsyncDataItem(
        {
          totalCount: currentData.totalCount,
          unfiledCount: currentData.unfiledCount,
          totalDocumentCount: currentData.totalDocumentCount,
          folders: updatedFolders,
        },
        AsyncDataItemState.LOADED
      ),
    };
  }),

  on(FolderActions.deleteFolderSuccessEvent, (state, { id }) => {
    const currentData = state.folder.data;

    // Remove the folder from the tree and count its contents
    const {
      folders: updatedFolders,
      deletedCount,
      deletedDocumentCount,
    } = removeFolderFromTree(currentData.folders, id);

    return {
      ...state,
      folder: wrapAsAsyncDataItem(
        {
          ...currentData,
          totalCount: currentData.totalCount - deletedCount,
          totalDocumentCount:
            currentData.totalDocumentCount - deletedDocumentCount,
          folders: updatedFolders,
        },
        AsyncDataItemState.LOADED
      ),
      selectedFolderId:
        state.selectedFolderId === id ? undefined : state.selectedFolderId,
    };
  }),

  // Folder UI state
  on(FolderActions.selectFolderCommand, (state, { folderId }) => ({
    ...state,
    selectedFolderId: folderId,
  })),
  on(FolderActions.toggleFolderExpandedCommand, (state, { folderId }) => ({
    ...state,
    expandedFolders: state.expandedFolders.includes(folderId)
      ? state.expandedFolders.filter((id) => id !== folderId)
      : [...state.expandedFolders, folderId],
  })),
  on(FolderActions.setDragOverFolderCommand, (state, { folderId }) => ({
    ...state,
    dragOverFolder: folderId,
  }))
);

// Helper functions for tree manipulation
function findFolderInTree(
  folders: FolderItem[],
  folderId: string
): FolderItem | null {
  for (const folder of folders) {
    if (folder.id === folderId) {
      return folder;
    }
    if (folder.children && folder.children.length > 0) {
      const found = findFolderInTree(folder.children, folderId);
      if (found) return found;
    }
  }
  return null;
}

function moveFolderInTree(
  folders: FolderItem[],
  updatedFolder: FolderItem
): FolderItem[] {
  // First, get the folder with its current children
  const folderToMove = findFolderInTree(folders, updatedFolder.id);
  if (!folderToMove) return folders;

  // Preserve the original children
  const folderWithChildren = {
    ...updatedFolder,
    children: folderToMove.children,
  };

  // Remove folder from its current location
  let result = removeFolderById(folders, updatedFolder.id);

  // Add folder to its new location
  if (updatedFolder.parentId) {
    // Add to specific parent
    result = addFolderToParent(
      result,
      folderWithChildren,
      updatedFolder.parentId
    );
  } else {
    // Add to root level
    result = [...result, folderWithChildren];
  }

  return result;
}

function removeFolderById(
  folders: FolderItem[],
  folderId: string
): FolderItem[] {
  return folders
    .filter((folder) => folder.id !== folderId)
    .map((folder) => {
      if (folder.children && folder.children.length > 0) {
        return {
          ...folder,
          children: removeFolderById(folder.children, folderId),
          childrenCount: folder.children.filter(
            (child) => child.id !== folderId
          ).length,
        };
      }
      return folder;
    });
}

function addFolderToParent(
  folders: FolderItem[],
  folderToAdd: FolderItem,
  parentId: string
): FolderItem[] {
  return folders.map((folder) => {
    if (folder.id === parentId) {
      return {
        ...folder,
        children: [...folder.children, folderToAdd],
        childrenCount: folder.childrenCount + 1,
      };
    }
    if (folder.children && folder.children.length > 0) {
      return {
        ...folder,
        children: addFolderToParent(folder.children, folderToAdd, parentId),
      };
    }
    return folder;
  });
}

function addFolderToTree(
  folders: FolderItem[],
  newFolder: FolderItem,
  parentId: string | undefined
): FolderItem[] {
  if (!parentId) {
    // Add to root level
    return [...folders, newFolder];
  }

  // Recursively find parent and add the new folder
  return folders.map((folder) => {
    if (folder.id === parentId) {
      return {
        ...folder,
        children: [...folder.children, newFolder],
        childrenCount: folder.childrenCount + 1,
      };
    }
    if (folder.children.length > 0) {
      return {
        ...folder,
        children: addFolderToTree(folder.children, newFolder, parentId),
      };
    }
    return folder;
  });
}

function updateFolderInTree(
  folders: FolderItem[],
  updatedFolder: FolderItem
): FolderItem[] {
  return folders.map((folder) => {
    if (folder.id === updatedFolder.id) {
      // Merge the updated folder with existing children
      // The updated folder from the server might not include the full children tree
      return {
        ...updatedFolder,
        children: folder.children, // Preserve existing children structure
        childrenCount: folder.childrenCount, // Preserve children count
      };
    }
    if (folder.children && folder.children.length > 0) {
      // Recursively update in children
      const updatedChildren = updateFolderInTree(
        folder.children,
        updatedFolder
      );
      // Always return a new object when we have children to ensure proper change detection
      return {
        ...folder,
        children: updatedChildren,
      };
    }
    return folder;
  });
}

function removeFolderFromTree(
  folders: FolderItem[],
  folderId: string
): {
  folders: FolderItem[];
  deletedCount: number;
  deletedDocumentCount: number;
} {
  let deletedCount = 0;
  let deletedDocumentCount = 0;

  const countFolderContents = (
    folder: FolderItem
  ): { folderCount: number; documentCount: number } => {
    let folderCount = 1; // Count this folder
    let documentCount = folder.documentCount;

    for (const child of folder.children) {
      const childCounts = countFolderContents(child);
      folderCount += childCounts.folderCount;
      documentCount += childCounts.documentCount;
    }

    return { folderCount, documentCount };
  };

  const filteredFolders = folders
    .filter((folder) => {
      if (folder.id === folderId) {
        const counts = countFolderContents(folder);
        deletedCount = counts.folderCount;
        deletedDocumentCount = counts.documentCount;
        return false;
      }
      return true;
    })
    .map((folder) => {
      if (folder.children.length > 0) {
        const result = removeFolderFromTree(folder.children, folderId);
        deletedCount += result.deletedCount;
        deletedDocumentCount += result.deletedDocumentCount;
        return {
          ...folder,
          children: result.folders,
          childrenCount: folder.childrenCount - result.deletedCount,
        };
      }
      return folder;
    });

  return { folders: filteredFolders, deletedCount, deletedDocumentCount };
}

function updateDocumentCountInTree(
  folders: FolderItem[],
  folderId: string,
  documentCountChange: number
): FolderItem[] {
  return folders.map((folder) => {
    if (folder.id === folderId) {
      return {
        ...folder,
        documentCount: folder.documentCount + documentCountChange,
      };
    }
    if (folder.children.length > 0) {
      return {
        ...folder,
        children: updateDocumentCountInTree(
          folder.children,
          folderId,
          documentCountChange
        ),
      };
    }
    return folder;
  });
}
