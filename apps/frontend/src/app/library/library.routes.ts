import { inject } from '@angular/core';
import { Routes } from '@angular/router';
import { Store } from '@ngrx/store';
import { ArchiveActions } from './archive/store/archive.actions';

export const libraryRoutes: Routes = [
  {
    path: '',
    loadComponent: () => import('./library-shell').then((m) => m.LibraryShell),
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./documents/components/document-list').then(
            (m) => m.DocumentListComponent
          ),
        data: { animation: 'documents' },
      },
      {
        path: 'archive',
        loadComponent: () =>
          import('./archive/components/archive').then(
            (m) => m.ArchiveComponent
          ),
        data: { animation: 'archive' },
        resolve: {
          init: () => {
            const store = inject(Store);
            store.dispatch(ArchiveActions.fetchArchiveCommand());
            return true;
          },
        },
      },
    ],
  },
];
