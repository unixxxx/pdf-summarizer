import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { FolderTreeDto } from '../dtos/folder-tree';
import { FolderItemDto } from '../dtos/folder-item';
import { FolderCreateDto } from '../dtos/folder-create';
import { FolderUpdateDto } from '../dtos/folder-update';

@Injectable({
  providedIn: 'root',
})
export class FolderService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = '/api/v1/folder';

  createFolder(folder: FolderCreateDto): Observable<FolderItemDto> {
    return this.http.post<FolderItemDto>(this.apiUrl, folder);
  }

  getFoldersTree(): Observable<FolderTreeDto> {
    return this.http.get<FolderTreeDto>(`${this.apiUrl}/tree`);
  }

  getFolder(folderId: string): Observable<FolderItemDto> {
    return this.http.get<FolderItemDto>(`${this.apiUrl}/${folderId}`);
  }

  updateFolder(
    folderId: string,
    folder: FolderUpdateDto
  ): Observable<FolderItemDto> {
    return this.http.patch<FolderItemDto>(`${this.apiUrl}/${folderId}`, folder);
  }

  deleteFolder(folderId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${folderId}`);
  }

  addDocumentsToFolder(
    folderId: string,
    documentIds: string[]
  ): Observable<FolderItemDto> {
    return this.http.post<FolderItemDto>(
      `${this.apiUrl}/${folderId}/documents`,
      { document_ids: documentIds }
    );
  }
}
