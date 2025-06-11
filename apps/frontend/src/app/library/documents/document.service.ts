import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Document, DocumentDto, PaginatedLibraryResponse } from './document.model';

export interface DocumentSearchCriteria {
  searchQuery?: string;
  tags?: string[];
  folderId?: string;
  unfiled?: boolean;
  limit?: number;
  offset?: number;
}

export type ExportFormat = 'markdown' | 'pdf' | 'text';

@Injectable({
  providedIn: 'root',
})
export class DocumentService {
  private http = inject(HttpClient);
  private baseUrl = '/api/v1/document';

  /**
   * Browse documents with summaries, search, and filtering
   */
  browse(criteria?: DocumentSearchCriteria): Observable<PaginatedLibraryResponse> {
    const params = this.buildParams(criteria);
    return this.http.get<PaginatedLibraryResponse>(this.baseUrl, { params });
  }

  /**
   * Get a specific document by ID
   */
  findById(id: string): Observable<Document> {
    return this.http
      .get<DocumentDto>(`${this.baseUrl}/${id}`)
      .pipe(map((dto) => Document.fromDto(dto)));
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
  getDownloadUrl(id: string): Observable<{ url: string; filename?: string }> {
    return this.http
      .get<{ download_url?: string; filename?: string }>(
        `/api/v1/storage/download/${id}`
      )
      .pipe(
        map((response) => ({
          url: response.download_url || '',
          filename: response.filename,
        }))
      );
  }

  /**
   * Export a summary in the specified format
   */
  exportSummary(summaryId: string, format: ExportFormat): Observable<Blob> {
    return this.http.get(`/api/v1/export/${summaryId}`, {
      params: { format },
      responseType: 'blob',
    });
  }


  private buildParams(criteria?: DocumentSearchCriteria): HttpParams {
    let params = new HttpParams();

    if (criteria?.searchQuery) {
      params = params.set('search', criteria.searchQuery);
    }

    if (criteria?.tags) {
      criteria.tags.forEach((tag) => {
        params = params.append('tags', tag);
      });
    }

    if (criteria?.folderId) {
      params = params.set('folder_id', criteria.folderId);
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