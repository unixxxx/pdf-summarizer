// API DTOs for archive endpoints

export interface ArchiveStatsDto {
  total_documents: number;
  total_folders: number;
  total_size: number;
  oldest_item_date: string | null;
}

export interface ArchivedDocumentDto {
  id: string;
  name: string;
  archived_at: string;
  user_id: string;
  file_size: number;
  page_count: number | null;
  folder_id: string | null;
  folder_name: string | null;
}

export interface ArchivedFolderDto {
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

export interface ArchivedFolderWithChildrenDto extends ArchivedFolderDto {
  children: ArchivedFolderWithChildrenDto[];
  documents: ArchivedDocumentDto[];
}

export interface RestoreFolderRequestDto {
  folder_id: string;
  restore_children: boolean;
  new_parent_id: string | null;
}

export interface RestoreDocumentRequestDto {
  document_ids: string[];
  folder_id: string | null;
}

export interface EmptyArchiveRequestDto {
  confirm: boolean;
  delete_all: boolean;
}
