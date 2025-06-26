import { AsyncDataItem } from '../../../../core/utils/async-data-item';
import { FolderTree } from './folder-tree';

export interface FolderState {
  folder: AsyncDataItem<FolderTree>;
  selectedFolderId: string | undefined;
  expandedFolders: string[];
  dragOverFolder: string | undefined;
}
