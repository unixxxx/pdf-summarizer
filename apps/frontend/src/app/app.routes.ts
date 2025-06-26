import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { loggedInGuard } from './core/guards/logged-in.guard';
import { provideEffects } from '@ngrx/effects';
import { provideState, Store } from '@ngrx/store';
import { inject } from '@angular/core';
import { TagActions } from './library/tag/store/tag.actions';
import { FolderActions } from './library/folder/store/folder.actions';
import { FolderEffects } from './library/folder/store/folder.effects';
import { folderFeature } from './library/folder/store/folder.feature';
import { tagFeature } from './library/tag/store/tag.feature';
import { TagEffects } from './library/tag/store/tag.effects';
import { uploadFeature } from './library/upload/store/upload.feature';
import { UploadEffects } from './library/upload/store/upload.effects';
import { archiveFeature } from './library/archive/store/archive.feature';
import { ArchiveEffects } from './library/archive/store/archive.effects';
import { documentFeature } from './library/documents/store/document.feature';
import { DocumentEffects } from './library/documents/store/document.effects';
import { DocumentActions } from './library/documents/store/document.actions';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () =>
      import('./auth/components/login/login').then((m) => m.Login),
    canActivate: [loggedInGuard],
  },
  {
    path: 'auth/callback',
    loadComponent: () =>
      import('./auth/components/auth-callback/auth-callback').then(
        (m) => m.AuthCallback
      ),
  },
  {
    path: 'auth/error',
    loadComponent: () =>
      import('./auth/components/auth-error/auth-error').then(
        (m) => m.AuthError
      ),
  },
  {
    path: '',
    loadComponent: () => import('./layout/layout').then((m) => m.Layout),
    canActivate: [authGuard],
    children: [
      {
        path: '',
        redirectTo: 'library',
        pathMatch: 'full',
      },
      {
        path: 'library',
        loadChildren: () =>
          import('./library/library.routes').then((m) => m.libraryRoutes),
        data: { animation: 'library' },
        providers: [
          provideState(folderFeature),
          provideState(tagFeature),
          provideState(uploadFeature),
          provideState(archiveFeature),
          provideState(documentFeature),
          provideEffects(
            FolderEffects,
            TagEffects,
            UploadEffects,
            ArchiveEffects,
            DocumentEffects
          ),
        ],
        resolve: {
          init: () => {
            const store = inject(Store);
            store.dispatch(FolderActions.fetchFoldersCommand());
            store.dispatch(TagActions.fetchTagsCommand());
            return true;
          },
        },
      },
      {
        path: 'chat',
        loadComponent: () => import('./chat/chat').then((m) => m.Chat),
        data: { animation: 'chat' },
      },
      {
        path: 'chat/:chatId',
        loadComponent: () => import('./chat/chat').then((m) => m.Chat),
        data: { animation: 'chat' },
      },
    ],
  },
];
