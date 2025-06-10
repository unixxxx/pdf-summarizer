import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Summary, Tag, SummaryDto, TagDto } from '../summary/summary.model';

// DTO interface for library API response
export interface LibraryItemDto {
  id: string;
  document_id: string;
  filename?: string;
  fileName?: string; // Legacy support
  file_size?: number;
  fileSize?: number; // Legacy support
  summary: string;
  word_count?: number;
  wordCount?: number; // Legacy support
  processing_time?: number;
  processingTime?: number; // Legacy support
  created_at?: string;
  createdAt?: string; // Legacy support
  tags?: TagDto[];
}

export interface LibraryItem {
  id: string;
  documentId: string;
  filename: string;
  fileSize: number;
  summary: Summary;
  createdAt: Date;
}

export interface LibrarySearchCriteria {
  searchQuery?: string;
  tags?: string[];
}

export type ExportFormat = 'markdown' | 'pdf' | 'text';

@Injectable({
  providedIn: 'root',
})
export class LibraryService {
  private http = inject(HttpClient);
  private baseUrl = '/api/v1/library';

  browse(criteria?: LibrarySearchCriteria): Observable<LibraryItem[]> {
    let params = new HttpParams();

    if (criteria?.searchQuery) {
      params = params.set('search', criteria.searchQuery);
    }

    if (criteria?.tags) {
      criteria.tags.forEach((tag) => {
        params = params.append('tags', tag);
      });
    }

    return this.http.get<LibraryItemDto[]>(`${this.baseUrl}`, { params }).pipe(
      map((dtos) =>
        dtos.map((dto) => {
          const summaryDto: SummaryDto = {
            id: dto.id,
            document_id: dto.document_id,
            content: dto.summary,
            word_count: dto.word_count || dto.wordCount || 0,
            processing_time: dto.processing_time || dto.processingTime || 0,
            created_at:
              dto.created_at || dto.createdAt || new Date().toISOString(),
            tags: dto.tags,
          };

          return {
            id: dto.id,
            documentId: dto.document_id,
            filename: dto.filename || dto.fileName || 'Unknown',
            fileSize: dto.file_size || dto.fileSize || 0,
            summary: Summary.fromDto(summaryDto),
            createdAt: new Date(dto.created_at || dto.createdAt || new Date()),
          };
        })
      )
    );
  }

  getTags(): Observable<Tag[]> {
    return this.http
      .get<TagDto[]>(`${this.baseUrl}/tags`)
      .pipe(map((dtos) => dtos.map((dto) => Tag.fromDto(dto))));
  }

  deleteDocument(documentId: string): Observable<void> {
    return this.http.delete<void>(`/api/v1/document/${documentId}`);
  }

  exportSummary(summaryId: string, format: ExportFormat): Observable<Blob> {
    return this.http.get(`${this.baseUrl}/export/${summaryId}`, {
      params: { format },
      responseType: 'blob',
    });
  }
}
