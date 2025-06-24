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
          provideEffects(FolderEffects, TagEffects),
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
        loadComponent: () =>
          import('./chat/chat.component').then((m) => m.ChatComponent),
        data: { animation: 'chat' },
      },
      {
        path: 'chat/:chatId',
        loadComponent: () =>
          import('./chat/chat.component').then((m) => m.ChatComponent),
        data: { animation: 'chat' },
      },
    ],
  },
];
