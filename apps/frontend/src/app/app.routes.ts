import { Routes } from '@angular/router';
import { authGuard } from './auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { 
    path: 'login', 
    loadComponent: () => import('./login/login.component').then(m => m.LoginComponent) 
  },
  {
    path: 'app',
    loadComponent: () => import('./layout/layout.component').then(m => m.LayoutComponent),
    canActivate: [authGuard],
    children: [
      { path: '', redirectTo: 'upload', pathMatch: 'full' },
      { 
        path: 'upload', 
        loadComponent: () => import('./upload/upload.component').then(m => m.UploadComponent) 
      },
      { 
        path: 'text', 
        loadComponent: () => import('./text-summarize/text-summarize.component').then(m => m.TextSummarizeComponent) 
      },
      { 
        path: 'history', 
        loadComponent: () => import('./history/history.component').then(m => m.HistoryComponent) 
      }
    ]
  },
  { 
    path: 'auth/callback', 
    loadComponent: () => import('./auth-callback/auth-callback.component').then(m => m.AuthCallbackComponent) 
  }
];