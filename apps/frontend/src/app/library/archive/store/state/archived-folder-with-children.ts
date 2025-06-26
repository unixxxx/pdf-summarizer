import { ToCamelCase } from '../../../../core/utils/transform';
import { ArchivedFolderWithChildrenDto } from '../../dtos/archived-folder-with-children';
import { ArchivedDocument, toArchivedDocument } from './archived-document';
import { toArchivedFolder } from './archived-folder';

/**
 * Archived folder with children type for the store
 */
export type ArchivedFolderWithChildren = Omit<
  ToCamelCase<ArchivedFolderWithChildrenDto>,
  'children' | 'documents'
> & {
  children: ArchivedFolderWithChildren[];
  documents: ArchivedDocument[];
};

/**
 * Convert ArchivedFolderWithChildrenDto to ArchivedFolderWithChildren
 */
export const toArchivedFolderWithChildren = (
  folder: ArchivedFolderWithChildrenDto
): ArchivedFolderWithChildren => ({
  ...toArchivedFolder(folder),
  children: folder.children.map(toArchivedFolderWithChildren),
  documents: folder.documents.map(toArchivedDocument),
});
