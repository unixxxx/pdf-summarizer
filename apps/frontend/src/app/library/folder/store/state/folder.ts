import { ToCamelCase } from '../../../../core/utils/transform';
import { FolderItemDto, FolderDto } from '../../dtos/folder';
import { Tag, toTag } from '../../../tag/store/state/tag';

export type FolderItem = Omit<
  ToCamelCase<FolderItemDto>,
  'children' | 'tags'
> & {
  children: FolderItem[];
  tags: Tag[];
};

export type Folder = Omit<ToCamelCase<FolderDto>, 'folders'> & {
  folders: FolderItem[];
};

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

export const toFolders = (folder: FolderDto): Folder => ({
  totalCount: folder.total_count,
  unfiledCount: folder.unfiled_count,
  totalDocumentCount: folder.total_document_count,
  folders: folder.folders.map(toFolderItem),
});
