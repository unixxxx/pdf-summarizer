import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { map } from 'rxjs/operators';
import { Summary, SummaryOptions, SummaryDto } from './summary.model';
import { DocumentMetadata } from '../library/documents/document.model';

@Injectable({
  providedIn: 'root',
})
export class SummaryService {
  private http = inject(HttpClient);
  private baseUrl = '/api/v1/summarization';

  createForDocument(
    documentId: string,
    options?: SummaryOptions
  ): Observable<Summary> {
    const params = {
      document_id: documentId,
      ...(options?.toRequestParams() || {}),
    };

    return this.http
      .post<SummaryDto>(`${this.baseUrl}`, params)
      .pipe(map((dto) => Summary.fromDto(dto)));
  }

  createForText(
    text: string,
    filename: string,
    options?: SummaryOptions
  ): Observable<Summary> {
    const params = {
      text,
      filename,
      ...(options?.toRequestParams() || {}),
    };

    return this.http
      .post<SummaryDto>(`${this.baseUrl}`, params)
      .pipe(map((dto) => Summary.fromDto(dto)));
  }

  uploadAndSummarize(
    file: File,
    options?: SummaryOptions
  ): Observable<Summary> {
    // Validate file first
    const metadata = new DocumentMetadata(file.name, file.size, file.type);
    if (!metadata.isValid) {
      return throwError(() => new Error(metadata.validationErrors.join('. ')));
    }

    const formData = new FormData();
    formData.append('file', file);

    if (options) {
      const params = options.toRequestParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          formData.append(key, value.toString());
        }
      });
    }

    return this.http
      .post<SummaryDto>(`${this.baseUrl}/upload`, formData)
      .pipe(map((dto) => Summary.fromDto(dto)));
  }

  export(
    summaryId: string,
    format: 'pdf' | 'markdown' | 'text'
  ): Observable<Blob> {
    return this.http.get(
      `/api/v1/export/${summaryId}?format=${format}`,
      {
        responseType: 'blob',
      }
    );
  }

  delete(summaryId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${summaryId}`);
  }
}
