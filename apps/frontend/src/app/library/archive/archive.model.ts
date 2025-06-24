export interface ArchiveStats {
  total_documents: number;
  total_folders: number;
  total_size: number;
  oldest_item_date: string | null;
}

export interface ArchivedDocument {
  id: string;
  name: string;
  archived_at: string;
  user_id: string;
  file_size: number;
  page_count: number | null;
  folder_id: string | null;
  folder_name: string | null;
}

export interface ArchivedFolder {
  id: string;
  name: string;
  archived_at: string;
  user_id: string;
  description: string | null;
  color: string | null;
  parent_id: string | null;
  parent_name: string | null;
  document_count: number;
  children_count: number;
}

export interface ArchivedFolderWithChildren extends ArchivedFolder {
  children: ArchivedFolderWithChildren[];
  documents: ArchivedDocument[];
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
