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
        data: { animation: 'summarize' }
      },
      {
        path: 'library',
        loadChildren: () =>
          import('./library/library.routes').then((m) => m.libraryRoutes),
        data: { animation: 'library' }
      },
      {
        path: 'chat',
        loadComponent: () =>
          import('./chat/chat.component').then((m) => m.ChatComponent),
        data: { animation: 'chat' }
      },
      {
        path: 'chat/:chatId',
        loadComponent: () =>
          import('./chat/chat.component').then((m) => m.ChatComponent),
        data: { animation: 'chat' }
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
