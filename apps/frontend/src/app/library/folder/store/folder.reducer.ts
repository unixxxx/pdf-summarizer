import { createReducer, on } from '@ngrx/store';
import { FolderState } from './state/folder-state';
import { FolderActions } from './folder.actions';
import {
  AsyncDataItemState,
  wrapAsAsyncDataItem,
} from '../../../core/utils/async-data-item';
import { FolderItem, toFolderItem } from './state/folder-item';
import { toFolderTree } from './state/folder-tree';
import { DocumentActions } from '../../documents/store/document.actions';
import { UploadActions } from '../../upload/store/upload.actions';

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
    folder: wrapAsAsyncDataItem(
      toFolderTree(folder),
      AsyncDataItemState.LOADED
    ),
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
    let updatedFolders = addFolderToTree(
      currentData.folders,
      newFolderItem,
      folder.parent_id
    );

    // If the new folder has documents, update ancestor counts
    if (newFolderItem.documentCount > 0 && folder.parent_id) {
      updatedFolders = updateDocumentCountInAncestors(
        updatedFolders,
        folder.parent_id,
        newFolderItem.documentCount
      );
    }

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
      // Calculate total document count for the moving folder and its descendants
      const countAllDocuments = (f: FolderItem): number => {
        let count = f.documentCount;
        for (const child of f.children) {
          count += countAllDocuments(child);
        }
        return count;
      };

      const totalDocumentCount = oldFolder ? countAllDocuments(oldFolder) : 0;

      // If parent changed, we need to move the folder
      updatedFolders = moveFolderInTree(
        [...currentData.folders],
        updatedFolderItem
      );

      // Update counts for old and new parent hierarchies
      if (totalDocumentCount > 0) {
        // Decrease counts in old parent hierarchy
        if (oldFolder.parentId) {
          updatedFolders = updateDocumentCountInAncestors(
            updatedFolders,
            oldFolder.parentId,
            -totalDocumentCount
          );
        }

        // Increase counts in new parent hierarchy
        if (updatedFolderItem.parentId) {
          updatedFolders = updateDocumentCountInAncestors(
            updatedFolders,
            updatedFolderItem.parentId,
            totalDocumentCount
          );
        }
      }
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

    // First find the parent of the folder being deleted
    const findParentId = (
      folders: FolderItem[],
      targetId: string,
      parentId: string | null = null
    ): string | null => {
      for (const folder of folders) {
        if (folder.id === targetId) {
          return parentId;
        }
        if (folder.children.length > 0) {
          const found = findParentId(folder.children, targetId, folder.id);
          if (found !== null) return found;
        }
      }
      return null;
    };

    const parentId = findParentId(currentData.folders, id);

    // Remove the folder from the tree and count its contents
    const {
      folders: updatedFolders,
      deletedCount,
      deletedDocumentCount,
    } = removeFolderFromTree(currentData.folders, id);

    // Update ancestor counts if documents were deleted
    let finalFolders = updatedFolders;
    if (deletedDocumentCount > 0 && parentId) {
      finalFolders = updateDocumentCountInAncestors(
        updatedFolders,
        parentId,
        -deletedDocumentCount
      );
    }

    return {
      ...state,
      folder: wrapAsAsyncDataItem(
        {
          ...currentData,
          totalCount: currentData.totalCount - deletedCount,
          totalDocumentCount:
            currentData.totalDocumentCount - deletedDocumentCount,
          folders: finalFolders,
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
  })),

  // Document operations
  on(FolderActions.addDocumentsToFolderSuccessEvent, (state, { from, to }) => {
    const currentData = state.folder.data;
    let updatedFolders = [...currentData.folders];

    // Since document_count includes all descendants, we need to update counts
    // for the destination folder and all its ancestors
    updatedFolders = updateDocumentCountInAncestors(updatedFolders, to, 1);

    // If moving from a folder, decrease counts for source folder and all its ancestors
    if (from && from !== '') {
      updatedFolders = updateDocumentCountInAncestors(updatedFolders, from, -1);
    }

    // Update unfiled count if documents were moved from or to unfiled
    let newUnfiledCount = currentData.unfiledCount;
    if (!from || from === '') {
      // Document was moved from unfiled
      newUnfiledCount -= 1;
    }

    return {
      ...state,
      folder: wrapAsAsyncDataItem(
        {
          ...currentData,
          unfiledCount: newUnfiledCount,
          folders: updatedFolders,
        },
        AsyncDataItemState.LOADED
      ),
    };
  }),

  // Handle document deletion
  on(DocumentActions.deleteDocumentSuccessEvent, (state, { folderId }) => {
    const currentData = state.folder.data;

    if (!folderId) {
      // Document was unfiled, decrease unfiled count
      return {
        ...state,
        folder: wrapAsAsyncDataItem(
          {
            ...currentData,
            unfiledCount: Math.max(0, currentData.unfiledCount - 1),
            totalDocumentCount: Math.max(0, currentData.totalDocumentCount - 1),
          },
          AsyncDataItemState.LOADED
        ),
      };
    }

    // Document was in a folder, update that folder and all its ancestors
    const updatedFolders = updateDocumentCountInAncestors(
      [...currentData.folders],
      folderId,
      -1
    );

    return {
      ...state,
      folder: wrapAsAsyncDataItem(
        {
          ...currentData,
          totalDocumentCount: Math.max(0, currentData.totalDocumentCount - 1),
          folders: updatedFolders,
        },
        AsyncDataItemState.LOADED
      ),
    };
  }),

  // Handle successful file upload - update counts if document has folder
  on(UploadActions.uploadFileSuccessEvent, (state, { folderId }) => {
    const currentData = state.folder.data;

    if (!folderId) {
      // Document was uploaded without folder, increase unfiled count
      return {
        ...state,
        folder: wrapAsAsyncDataItem(
          {
            ...currentData,
            unfiledCount: currentData.unfiledCount + 1,
            totalDocumentCount: currentData.totalDocumentCount + 1,
          },
          AsyncDataItemState.LOADED
        ),
      };
    }

    // Document was uploaded to a folder, update that folder and all its ancestors
    const updatedFolders = updateDocumentCountInAncestors(
      [...currentData.folders],
      folderId,
      1
    );

    return {
      ...state,
      folder: wrapAsAsyncDataItem(
        {
          ...currentData,
          totalDocumentCount: currentData.totalDocumentCount + 1,
          folders: updatedFolders,
        },
        AsyncDataItemState.LOADED
      ),
    };
  }),

  // Handle successful text document creation - update counts if document has folder
  on(UploadActions.createTextDocumentSuccessEvent, (state, { folderId }) => {
    const currentData = state.folder.data;

    if (!folderId) {
      // Document was created without folder, increase unfiled count
      return {
        ...state,
        folder: wrapAsAsyncDataItem(
          {
            ...currentData,
            unfiledCount: currentData.unfiledCount + 1,
            totalDocumentCount: currentData.totalDocumentCount + 1,
          },
          AsyncDataItemState.LOADED
        ),
      };
    }

    // Document was created in a folder, update that folder and all its ancestors
    const updatedFolders = updateDocumentCountInAncestors(
      [...currentData.folders],
      folderId,
      1
    );

    return {
      ...state,
      folder: wrapAsAsyncDataItem(
        {
          ...currentData,
          totalDocumentCount: currentData.totalDocumentCount + 1,
          folders: updatedFolders,
        },
        AsyncDataItemState.LOADED
      ),
    };
  })
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

function updateDocumentCountInAncestors(
  folders: FolderItem[],
  folderId: string,
  documentCountChange: number
): FolderItem[] {
  // First, find the path from root to the target folder
  const findPath = (
    items: FolderItem[],
    targetId: string,
    path: string[] = []
  ): string[] | null => {
    for (const folder of items) {
      if (folder.id === targetId) {
        return [...path, folder.id];
      }
      if (folder.children.length > 0) {
        const childPath = findPath(folder.children, targetId, [
          ...path,
          folder.id,
        ]);
        if (childPath) return childPath;
      }
    }
    return null;
  };

  const pathToFolder = findPath(folders, folderId);
  if (!pathToFolder) return folders;

  // Update counts for all folders in the path
  const updateFolders = (items: FolderItem[]): FolderItem[] => {
    return items.map((folder) => {
      const shouldUpdate = pathToFolder.includes(folder.id);
      const updatedFolder = shouldUpdate
        ? {
            ...folder,
            documentCount: Math.max(
              0,
              folder.documentCount + documentCountChange
            ),
          }
        : folder;

      // Recursively update children
      if (updatedFolder.children.length > 0) {
        return {
          ...updatedFolder,
          children: updateFolders(updatedFolder.children),
        };
      }
      return updatedFolder;
    });
  };

  return updateFolders(folders);
}
