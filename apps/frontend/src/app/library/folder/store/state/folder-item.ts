import { ToCamelCase } from '../../../../core/utils/transform';
import { FolderItemDto } from '../../dtos/folder-item';
import { Tag, toTag } from '../../../tag/store/state/tag';

/**
 * Folder item type for the store
 * Represents a single folder with camelCase properties
 */
export type FolderItem = Omit<
  ToCamelCase<FolderItemDto>,
  'children' | 'tags'
> & {
  children: FolderItem[];
  tags: Tag[];
};

/**
 * Convert FolderItemDto to FolderItem
 */
export const toFolderItem = (folder: FolderItemDto): FolderItem => ({
  id: folder.id,
  name: folder.name,
  description: folder.description,
  color: folder.color,
  parentId: folder.parent_id,
  createdAt: folder.created_at,
  updatedAt: folder.updated_at,
  documentCount: folder.document_count,
  childrenCount: folder.children_count,
  children: folder.children?.map(toFolderItem) ?? [],
  tags: folder.tags.map(toTag),
});
