import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import {
  TrashStats,
  TrashedDocument,
  TrashedFolderWithChildren,
} from './trash.model';

@Injectable({
  providedIn: 'root',
})
export class TrashService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = '/api/v1/trash';

  getTrashStats(): Observable<TrashStats> {
    return this.http.get<TrashStats>(`${this.apiUrl}/stats`);
  }

  getTrashedDocuments(): Observable<TrashedDocument[]> {
    return this.http.get<TrashedDocument[]>(`${this.apiUrl}/documents`);
  }

  getTrashedFolders(): Observable<TrashedFolderWithChildren[]> {
    return this.http.get<TrashedFolderWithChildren[]>(`${this.apiUrl}/folders`);
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  restoreFolder(request: any): Observable<void> {
    return this.http.post<void>(`${this.apiUrl}/restore/folder`, request);
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  restoreDocuments(request: any): Observable<void> {
    return this.http.post<void>(`${this.apiUrl}/restore/documents`, request);
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  emptyTrash(request: any): Observable<void> {
    return this.http.post<void>(`${this.apiUrl}/empty`, request);
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  deleteDocuments(request: any): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/documents`, {
      body: request,
    });
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  deleteFolder(request: any): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/folder`, {
      body: request,
    });
  }
}