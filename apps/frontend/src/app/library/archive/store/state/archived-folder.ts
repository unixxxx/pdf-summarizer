import { ToCamelCase } from '../../../../core/utils/transform';
import { ArchivedFolderDto } from '../../dtos/archived-folder';

/**
 * Archived folder type for the store
 */
export type ArchivedFolder = ToCamelCase<ArchivedFolderDto>;

/**
 * Convert ArchivedFolderDto to ArchivedFolder
 */
export const toArchivedFolder = (
  folder: ArchivedFolderDto
): ArchivedFolder => ({
  id: folder.id,
  name: folder.name,
  archivedAt: folder.archived_at,
  userId: folder.user_id,
  description: folder.description,
  color: folder.color,
  parentId: folder.parent_id,
  parentName: folder.parent_name,
  documentCount: folder.document_count,
  childrenCount: folder.children_count,
});
