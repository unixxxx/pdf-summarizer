import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Document, DocumentDto } from './document.model';

@Injectable({
  providedIn: 'root',
})
export class DocumentService {
  private http = inject(HttpClient);
  private baseUrl = '/api/v1/documents';

  findById(id: string): Observable<Document> {
    return this.http
      .get<DocumentDto>(`${this.baseUrl}/${id}`)
      .pipe(map((dto) => Document.fromDto(dto)));
  }

  findAll(): Observable<Document[]> {
    return this.http
      .get<DocumentDto[]>(this.baseUrl)
      .pipe(map((dtos) => dtos.map((dto) => Document.fromDto(dto))));
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}`);
  }

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
}
