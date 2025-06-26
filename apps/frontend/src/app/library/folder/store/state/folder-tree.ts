import { ToCamelCase } from '../../../../core/utils/transform';
import { FolderTreeDto } from '../../dtos/folder-tree';
import { FolderItem, toFolderItem } from './folder-item';

/**
 * Folder tree type for the store
 * Represents the entire folder hierarchy with metadata
 */
export type FolderTree = Omit<ToCamelCase<FolderTreeDto>, 'folders'> & {
  folders: FolderItem[];
};

/**
 * Convert FolderTreeDto to FolderTree
 */
export const toFolderTree = (folder: FolderTreeDto): FolderTree => ({
  totalCount: folder.total_count,
  unfiledCount: folder.unfiled_count,
  totalDocumentCount: folder.total_document_count,
  folders: folder.folders.map(toFolderItem),
});
