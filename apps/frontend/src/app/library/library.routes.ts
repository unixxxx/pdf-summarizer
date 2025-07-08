import { inject } from '@angular/core';
import { ActivatedRouteSnapshot, Routes } from '@angular/router';
import { Store } from '@ngrx/store';
import { ArchiveActions } from './archive/store/archive.actions';
import { DocumentActions } from './documents/store/document.actions';
import { FolderActions } from './folder/store/folder.actions';

export const libraryRoutes: Routes = [
  {
    path: '',
    loadComponent: () => import('./library-shell').then((m) => m.LibraryShell),
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./documents/components/document-list').then(
            (m) => m.DocumentList
          ),
        data: { animation: 'documents' },
        resolve: {
          init: () => {
            const store = inject(Store);
            store.dispatch(
              DocumentActions.fetchDocumentsCommand({
                criteria: {},
              })
            );
            return true;
          },
        },
      },
      {
        path: 'unfiled',
        pathMatch: 'full',
        loadComponent: () =>
          import('./documents/components/document-list').then(
            (m) => m.DocumentList
          ),
        data: { animation: 'documents' },
        resolve: {
          init: () => {
            const store = inject(Store);
            store.dispatch(
              DocumentActions.fetchDocumentsCommand({
                criteria: {
                  unfiled: true,
                },
              })
            );
            return true;
          },
        },
      },
      {
        path: 'archive',
        pathMatch: 'full',
        loadComponent: () =>
          import('./archive/components/archive').then((m) => m.Archive),
        data: { animation: 'archive' },
        resolve: {
          init: () => {
            const store = inject(Store);
            store.dispatch(ArchiveActions.fetchArchiveCommand());
            return true;
          },
        },
      },
      {
        path: ':folderId',
        loadComponent: () =>
          import('./documents/components/document-list').then(
            (m) => m.DocumentList
          ),
        data: { animation: 'documents' },
        resolve: {
          init: (route: ActivatedRouteSnapshot) => {
            const store = inject(Store);
            const folderId = route.paramMap.get('folderId') ?? undefined;
            store.dispatch(
              DocumentActions.fetchDocumentsCommand({
                criteria: {
                  folder_id: folderId,
                },
              })
            );
            store.dispatch(FolderActions.selectFolderCommand({ folderId }));
            return true;
          },
        },
      },
    ],
  },
];
