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
