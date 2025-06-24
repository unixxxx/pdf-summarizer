import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import {
  FolderCreateDto,
  FolderDto,
  FolderItemDto,
  FolderUpdateDto,
} from '../dtos/folder';

@Injectable({
  providedIn: 'root',
})
export class FolderService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = '/api/v1/folder';

  createFolder(folder: FolderCreateDto): Observable<FolderItemDto> {
    return this.http.post<FolderItemDto>(this.apiUrl, folder);
  }

  getFoldersTree(): Observable<FolderDto> {
    return this.http.get<FolderDto>(`${this.apiUrl}/tree`);
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
}
