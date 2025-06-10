import { Routes } from '@angular/router';
import { authGuard } from './auth/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  {
    path: 'login',
    loadComponent: () =>
      import('./auth/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'app',
    loadComponent: () =>
      import('./layout/layout.component').then((m) => m.LayoutComponent),
    canActivate: [authGuard],
    children: [
      { path: '', redirectTo: 'summarize', pathMatch: 'full' },
      {
        path: 'summarize',
        loadComponent: () =>
          import('./summary/summarize/summarize.component').then(
            (m) => m.SummarizeComponent
          ),
      },
      {
        path: 'library',
        loadComponent: () =>
          import('./documents/library/library.component').then(
            (m) => m.LibraryComponent
          ),
      },
      {
        path: 'chat',
        loadComponent: () =>
          import('./chat/chat.component').then((m) => m.ChatComponent),
      },
      {
        path: 'chat/:chatId',
        loadComponent: () =>
          import('./chat/chat.component').then((m) => m.ChatComponent),
      },
    ],
  },
  {
    path: 'auth/callback',
    loadComponent: () =>
      import('./auth/auth-callback/auth-callback.component').then(
        (m) => m.AuthCallbackComponent
      ),
  },
  {
    path: 'auth/error',
    loadComponent: () =>
      import('./auth/auth-error/auth-error.component').then(
        (m) => m.AuthErrorComponent
      ),
  },
];
