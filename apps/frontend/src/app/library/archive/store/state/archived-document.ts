import { ToCamelCase } from '../../../../core/utils/transform';
import { ArchivedDocumentDto } from '../../dtos/archived-document';

/**
 * Archived document type for the store
 */
export type ArchivedDocument = ToCamelCase<ArchivedDocumentDto>;

/**
 * Convert ArchivedDocumentDto to ArchivedDocument
 */
export const toArchivedDocument = (
  doc: ArchivedDocumentDto
): ArchivedDocument => ({
  id: doc.id,
  name: doc.name,
  archivedAt: doc.archived_at,
  userId: doc.user_id,
  fileSize: doc.file_size,
  pageCount: doc.page_count,
  folderId: doc.folder_id,
  folderName: doc.folder_name,
});
