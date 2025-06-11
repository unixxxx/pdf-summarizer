export interface Folder {
  id: string;
  userId?: string;
  user_id?: string; // Backend returns snake_case
  name: string;
  description?: string;
  color?: string;
  parentId?: string;
  parent_id?: string; // Backend returns snake_case
  createdAt?: string;
  created_at?: string; // Backend returns snake_case
  updatedAt?: string;
  updated_at?: string; // Backend returns snake_case
  documentCount?: number;
  document_count?: number; // Backend returns snake_case
  childrenCount?: number;
  children_count?: number; // Backend returns snake_case
}

export interface FolderWithChildren extends Folder {
  children: FolderWithChildren[];
}

export interface FolderTree {
  folders: FolderWithChildren[];
  totalCount?: number;
  total_count?: number; // Backend returns snake_case
  unfiledCount?: number;
  unfiled_count?: number; // Backend returns snake_case
  totalDocumentCount?: number;
  total_document_count?: number; // Backend returns snake_case
}

export interface CreateFolderRequest {
  name: string;
  description?: string;
  color?: string;
  parentId?: string | null;
}

export interface UpdateFolderRequest {
  name?: string;
  description?: string;
  color?: string;
  parentId?: string | null;
}

export interface AddDocumentsToFolderRequest {
  documentIds: string[];
}

export interface RemoveDocumentsFromFolderRequest {
  documentIds: string[];
}

export interface MoveFolderRequest {
  parentId?: string;
}
