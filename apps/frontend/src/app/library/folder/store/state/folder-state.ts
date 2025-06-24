import { AsyncDataItem } from '../../../../core/utils/async-data-item';
import { Folder } from './folder';

export interface FolderState {
  folder: AsyncDataItem<Folder>;
  selectedFolderId: string | null;
  expandedFolders: string[];
  dragOverFolder: string | null;
}
