import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { DocumentDetailDto } from '../dtos/document-detail';
import { DocumentsListDto } from '../dtos/documents-list-response';
import { DocumentSearchCriteria } from '../dtos/document-search-criteria';
import { ExportFormat } from '../dtos/export-format';

@Injectable({
  providedIn: 'root',
})
export class DocumentService {
  private http = inject(HttpClient);
  private baseUrl = '/api/v1/document';

  /**
   * Browse documents with summaries, search, and filtering
   */
  browse(criteria?: DocumentSearchCriteria): Observable<DocumentsListDto> {
    const params = this.buildParams(criteria);
    return this.http.get<DocumentsListDto>(this.baseUrl, { params });
  }

  /**
   * Get a specific document by ID
   */
  getById(id: string): Observable<DocumentDetailDto> {
    return this.http.get<DocumentDetailDto>(`${this.baseUrl}/${id}`);
  }

  /**
   * Delete a document
   */
  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}`);
  }

  /**
   * Get document download URL
   */
  getDownloadUrl(
    id: string
  ): Observable<{ download_url: string; filename?: string }> {
    return this.http.get<{ download_url: string; filename?: string }>(
      `/api/v1/storage/download/${id}`
    );
  }

  /**
   * Export a document in the specified format
   */
  exportDocument(documentId: string, format: ExportFormat): Observable<Blob> {
    return this.http.get(`${this.baseUrl}/${documentId}/export`, {
      params: { format },
      responseType: 'blob',
    });
  }

  /**
   * Download document
   */
  download(documentId: string): Observable<Blob> {
    return this.http.get(`/api/v1/storage/download/${documentId}/file`, {
      responseType: 'blob',
    });
  }

  /**
   * Update document (e.g., move to folder)
   */
  updateDocument(
    documentId: string,
    update: { folder_id?: string }
  ): Observable<DocumentDetailDto> {
    return this.http.patch<DocumentDetailDto>(
      `${this.baseUrl}/${documentId}`,
      update
    );
  }

  /**
   * Retry processing for a failed document
   */
  retryProcessing(documentId: string): Observable<{
    document_id: string;
    job_id: string;
    status: string;
    message: string;
  }> {
    return this.http.post<{
      document_id: string;
      job_id: string;
      status: string;
      message: string;
    }>(`${this.baseUrl}/${documentId}/retry`, {});
  }

  /**
   * Get suggestions for organizing unfiled documents into folders based on tag similarity
   */
  getOrganizationSuggestions(): Observable<{
    suggestions: Array<{
      document_id: string;
      document_name: string;
      document_tags: string[];
      suggested_folder_id: string;
      suggested_folder_name: string;
      folder_tags: string[];
      similarity_score: number;
      matching_tags: string[];
    }>;
    total_unfiled: number;
    total_with_tags: number;
  }> {
    return this.http.get<{
      suggestions: Array<{
        document_id: string;
        document_name: string;
        document_tags: string[];
        suggested_folder_id: string;
        suggested_folder_name: string;
        folder_tags: string[];
        similarity_score: number;
        matching_tags: string[];
      }>;
      total_unfiled: number;
      total_with_tags: number;
    }>(`${this.baseUrl}/organize/suggestions`);
  }

  /**
   * Apply document organization by moving selected documents to their assigned folders
   */
  applyOrganization(
    assignments: Array<{
      documentId: string;
      folderId: string;
    }>
  ): Observable<{
    message: string;
    organized_count: number;
    errors?: string[];
  }> {
    return this.http.post<{
      message: string;
      organized_count: number;
      errors?: string[];
    }>(
      `${this.baseUrl}/organize/apply`,
      assignments.map((assignment) => ({
        document_id: assignment.documentId,
        folder_id: assignment.folderId,
      }))
    );
  }

  private buildParams(criteria?: DocumentSearchCriteria): HttpParams {
    let params = new HttpParams();

    if (criteria?.search) {
      params = params.set('search', criteria.search);
    }

    if (criteria?.folder_id) {
      params = params.set('folder_id', criteria.folder_id);
    }

    if (criteria?.unfiled) {
      params = params.set('unfiled', 'true');
    }

    if (criteria?.limit) {
      params = params.set('limit', criteria.limit.toString());
    }

    if (criteria?.offset) {
      params = params.set('offset', criteria.offset.toString());
    }

    return params;
  }
}
