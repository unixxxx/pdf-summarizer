import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { TagDto } from '../dtos/tag';

@Injectable({
  providedIn: 'root',
})
export class TagService {
  private http = inject(HttpClient);
  private baseUrl = '/api/v1/tag';

  /**
   * Get all tags with document counts
   */
  getTags(): Observable<TagDto[]> {
    return this.http.get<TagDto[]>(this.baseUrl);
  }
}
