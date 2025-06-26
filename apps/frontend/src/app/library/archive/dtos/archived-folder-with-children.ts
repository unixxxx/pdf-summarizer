import { ArchivedFolderDto } from './archived-folder';
import { ArchivedDocumentDto } from './archived-document';

/**
 * Archived folder with children DTO
 * Represents a folder with its nested folders and documents
 */
export interface ArchivedFolderWithChildrenDto extends ArchivedFolderDto {
  children: ArchivedFolderWithChildrenDto[];
  documents: ArchivedDocumentDto[];
}
