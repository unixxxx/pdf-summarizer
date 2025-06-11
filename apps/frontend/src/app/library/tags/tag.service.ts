import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Tag } from './tag.model';
import { TagDto } from '../../summary/summary.model';

@Injectable({
  providedIn: 'root',
})
export class TagService {
  private http = inject(HttpClient);
  private baseUrl = '/api/v1/tag';

  /**
   * Get all tags with document counts
   */
  findAll(): Observable<Tag[]> {
    return this.http
      .get<TagDto[]>(this.baseUrl)
      .pipe(map((dtos) => dtos.map((dto) => Tag.fromDto(dto))));
  }

  /**
   * Generate tags for a document
   */
  generateTags(documentId: string): Observable<Tag[]> {
    return this.http
      .post<TagDto[]>(`${this.baseUrl}/generate`, { document_id: documentId })
      .pipe(map((dtos) => dtos.map((dto) => Tag.fromDto(dto))));
  }

  /**
   * Update a tag
   */
  update(tagId: string, updates: { name?: string; color?: string }): Observable<Tag> {
    return this.http
      .put<TagDto>(`${this.baseUrl}/${tagId}`, updates)
      .pipe(map((dto) => Tag.fromDto(dto)));
  }

  /**
   * Delete a tag
   */
  delete(tagId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${tagId}`);
  }
}