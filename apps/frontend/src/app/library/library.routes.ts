import { Routes } from '@angular/router';

export const libraryRoutes: Routes = [
  {
    path: '',
    loadComponent: () => import('./library-shell').then((m) => m.LibraryShell),
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./documents/components/document-list.component').then(
            (m) => m.DocumentListComponent
          ),
        data: { animation: 'documents' },
      },
      {
        path: 'archive',
        loadComponent: () =>
          import('./archive/components/archive.component').then(
            (m) => m.ArchiveComponent
          ),
        data: { animation: 'archive' },
      },
    ],
  },
];
