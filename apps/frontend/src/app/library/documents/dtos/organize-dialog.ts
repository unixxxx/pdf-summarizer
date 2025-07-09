/**
 * Types for document organization suggestions and dialog responses
 */

export interface OrganizeSuggestion {
  document_id: string;
  document_name: string;
  document_tags: string[];
  suggested_folder_id: string;
  suggested_folder_name: string;
  folder_tags: string[];
  similarity_score: number;
  matching_tags: string[];
}

export interface DocumentAssignment {
  document_id: string;
  folder_id: string;
}

export interface OrganizeDialogResult {
  organize: boolean;
  selectedAssignments: Array<{
    documentId: string;
    folderId: string;
  }>;
}