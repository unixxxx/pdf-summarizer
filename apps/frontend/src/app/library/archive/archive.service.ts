import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import {
  ArchiveStats,
  ArchivedDocument,
  ArchivedFolderWithChildren,
} from './archive.model';

@Injectable({
  providedIn: 'root',
})
export class ArchiveService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = '/api/v1/archive';

  getArchiveStats(): Observable<ArchiveStats> {
    return this.http.get<ArchiveStats>(`${this.apiUrl}/stats`);
  }

  getArchivedDocuments(): Observable<ArchivedDocument[]> {
    return this.http.get<ArchivedDocument[]>(`${this.apiUrl}/documents`);
  }

  getArchivedFolders(): Observable<ArchivedFolderWithChildren[]> {
    return this.http.get<ArchivedFolderWithChildren[]>(
      `${this.apiUrl}/folders`
    );
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
  emptyArchive(request: any): Observable<void> {
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
