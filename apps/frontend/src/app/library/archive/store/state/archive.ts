import { ToCamelCase } from '../../../../core/utils/transform';
import {
  ArchivedDocumentDto,
  ArchivedFolderDto,
  ArchivedFolderWithChildrenDto,
  ArchiveStatsDto,
} from '../../dtos/archive';

// Component interfaces
export type ArchiveStats = ToCamelCase<ArchiveStatsDto>;

export type ArchivedDocument = ToCamelCase<ArchivedDocumentDto>;

export type ArchivedFolder = ToCamelCase<ArchivedFolderDto>;

export type ArchivedFolderWithChildren = Omit<
  ToCamelCase<ArchivedFolderWithChildrenDto>,
  'children' | 'documents'
> & {
  children: ArchivedFolderWithChildren[];
  documents: ArchivedDocument[];
};

export interface Archive {
  stats: ArchiveStats;
  folders: ArchivedFolderWithChildren[];
  documents: ArchivedDocument[];
}

export interface ArchiveItem {
  id: string;
  name: string;
  type: 'folder' | 'document';
  archivedAt: string;
  parentId?: string;
  documentCount?: number;
  childrenCount?: number;
}

export interface RestoreFolderRequest {
  folderId: string;
  restoreChildren: boolean;
  newParentId: string | null;
}

export interface RestoreDocumentRequest {
  documentIds: string[];
  folderId: string | null;
}

export interface EmptyArchiveRequest {
  confirm: boolean;
  deleteAll: boolean;
}

// Transformation functions
export const toArchiveStats = (stats: ArchiveStatsDto): ArchiveStats => ({
  totalDocuments: stats.total_documents,
  totalFolders: stats.total_folders,
  totalSize: stats.total_size,
  oldestItemDate: stats.oldest_item_date,
});

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

export const toArchivedFolderWithChildren = (
  folder: ArchivedFolderWithChildrenDto
): ArchivedFolderWithChildren => ({
  ...toArchivedFolder(folder),
  children: folder.children.map(toArchivedFolderWithChildren),
  documents: folder.documents.map(toArchivedDocument),
});
