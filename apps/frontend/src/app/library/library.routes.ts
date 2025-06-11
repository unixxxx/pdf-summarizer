import { Routes } from '@angular/router';

export const libraryRoutes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./library-shell.component').then((m) => m.LibraryShellComponent),
    data: { animation: 'library' }
  },
  {
    path: 'trash',
    loadComponent: () =>
      import('./trash/components/trash.component').then((m) => m.TrashComponent),
    data: { animation: 'trash' }
  },
];
