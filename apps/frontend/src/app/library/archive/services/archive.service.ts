import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { ArchiveStatsDto } from '../dtos/archive-stats';
import { ArchivedDocumentDto } from '../dtos/archived-document';
import { ArchivedFolderWithChildrenDto } from '../dtos/archived-folder-with-children';
import { RestoreFolderRequestDto } from '../dtos/restore-folder-request';
import { RestoreDocumentRequestDto } from '../dtos/restore-document-request';
import { EmptyArchiveRequestDto } from '../dtos/empty-archive-request';
import { ArchiveStats, toArchiveStats } from '../store/state/archive-stats';
import {
  ArchivedDocument,
  toArchivedDocument,
} from '../store/state/archived-document';
import {
  ArchivedFolderWithChildren,
  toArchivedFolderWithChildren,
} from '../store/state/archived-folder-with-children';

@Injectable({
  providedIn: 'root',
})
export class ArchiveService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = '/api/v1/archive';

  getArchiveStats(): Observable<ArchiveStats> {
    return this.http
      .get<ArchiveStatsDto>(`${this.apiUrl}/stats`)
      .pipe(map(toArchiveStats));
  }

  getArchivedDocuments(): Observable<ArchivedDocument[]> {
    return this.http
      .get<ArchivedDocumentDto[]>(`${this.apiUrl}/documents`)
      .pipe(map((docs) => docs.map(toArchivedDocument)));
  }

  getArchivedFolders(): Observable<ArchivedFolderWithChildren[]> {
    return this.http
      .get<ArchivedFolderWithChildrenDto[]>(`${this.apiUrl}/folders`)
      .pipe(map((folders) => folders.map(toArchivedFolderWithChildren)));
  }

  restoreFolder(request: RestoreFolderRequestDto): Observable<void> {
    return this.http.post<void>(`${this.apiUrl}/restore/folder`, request);
  }

  restoreDocuments(request: RestoreDocumentRequestDto): Observable<void> {
    return this.http.post<void>(`${this.apiUrl}/restore/documents`, request);
  }

  emptyArchive(request: EmptyArchiveRequestDto): Observable<void> {
    return this.http.post<void>(`${this.apiUrl}/empty`, request);
  }

  deleteDocuments(request: { document_ids: string[] }): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/documents`, {
      body: request,
    });
  }

  deleteFolder(request: {
    folder_id: string;
    delete_children: boolean;
  }): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/folder`, {
      body: request,
    });
  }
}
