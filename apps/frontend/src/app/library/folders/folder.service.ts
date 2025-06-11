import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import {
  AddDocumentsToFolderRequest,
  CreateFolderRequest,
  Folder,
  FolderTree,
  MoveFolderRequest,
  RemoveDocumentsFromFolderRequest,
  UpdateFolderRequest,
} from './folder.model';

@Injectable({
  providedIn: 'root',
})
export class FolderService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = '/api/v1/folder';

  createFolder(folder: CreateFolderRequest): Observable<Folder> {
    return this.http.post<Folder>(this.apiUrl, {
      name: folder.name,
      description: folder.description,
      color: folder.color,
      parent_id: folder.parentId
    });
  }

  getFoldersTree(): Observable<FolderTree> {
    return this.http.get<FolderTree>(`${this.apiUrl}/tree`);
  }

  getFolder(folderId: string): Observable<Folder> {
    return this.http.get<Folder>(`${this.apiUrl}/${folderId}`);
  }

  updateFolder(
    folderId: string,
    folder: UpdateFolderRequest
  ): Observable<Folder> {
    return this.http.patch<Folder>(`${this.apiUrl}/${folderId}`, {
      name: folder.name,
      description: folder.description,
      color: folder.color,
      parent_id: folder.parentId
    });
  }

  deleteFolder(folderId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${folderId}`);
  }

  addDocumentsToFolder(
    folderId: string,
    request: AddDocumentsToFolderRequest
  ): Observable<Folder> {
    return this.http.post<Folder>(
      `${this.apiUrl}/${folderId}/documents`,
      { document_ids: request.documentIds }
    );
  }

  removeDocumentsFromFolder(
    folderId: string,
    request: RemoveDocumentsFromFolderRequest
  ): Observable<Folder> {
    return this.http.delete<Folder>(`${this.apiUrl}/${folderId}/documents`, {
      body: { document_ids: request.documentIds },
    });
  }


  moveFolder(folderId: string, request: MoveFolderRequest): Observable<Folder> {
    return this.http.post<Folder>(`${this.apiUrl}/${folderId}/move`, {
      parent_id: request.parentId
    });
  }
}
