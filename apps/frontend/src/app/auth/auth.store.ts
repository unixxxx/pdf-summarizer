import { inject, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { of } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { tapResponse } from '@ngrx/operators';
import {
  patchState,
  signalStore,
  withComputed,
  withMethods,
  withState,
  withHooks,
} from '@ngrx/signals';
import { rxMethod } from '@ngrx/signals/rxjs-interop';

export interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
}

interface AuthState {
  user: User | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  isLoading: false,
  error: null,
};

export const AuthStore = signalStore(
  { providedIn: 'root' },
  withState(initialState),
  withComputed((store) => ({
    isAuthenticated: computed(() => !!store.user()),
  })),
  withMethods((store) => {
    const http = inject(HttpClient);
    const router = inject(Router);

    return {
      initializeAuth(): void {
        const token = localStorage.getItem('access_token');
        if (token) {
          // Try to restore user from localStorage first
          const cachedUser = localStorage.getItem('auth_user');
          if (cachedUser) {
            const user = JSON.parse(cachedUser);
            patchState(store, { user });
          }
          // Then refresh from server
          this.loadUser();
        }
      },

      loadUser: rxMethod<void>(
        switchMap(() => {
          const token = localStorage.getItem('access_token');
          if (!token) {
            patchState(store, { user: null });
            return of(null);
          }

          patchState(store, { isLoading: true, error: null });

          return http.get<User>('/api/v1/auth/me').pipe(
            tapResponse({
              next: (user) => {
                patchState(store, { user, isLoading: false });
                localStorage.setItem('auth_user', JSON.stringify(user));
              },
              error: () => {
                localStorage.removeItem('access_token');
                localStorage.removeItem('auth_user');
                patchState(store, {
                  user: null,
                  isLoading: false,
                  error: 'Failed to load user',
                });
              },
            })
          );
        })
      ),

      login: rxMethod<'google' | 'github'>(
        switchMap((provider) => {
          patchState(store, { isLoading: true, error: null });
          
          return http.get<{ authorization_url: string; state: string }>(
            `/api/v1/auth/login/${provider}`
          ).pipe(
            tapResponse({
              next: (response) => {
                // Redirect to the OAuth provider's authorization URL
                window.location.href = response.authorization_url;
              },
              error: (error) => {
                patchState(store, { 
                  isLoading: false, 
                  error: 'Failed to initiate login' 
                });
                console.error('Login error:', error);
              },
            })
          );
        })
      ),

      handleCallback: rxMethod<string>(
        switchMap((token) => {
          localStorage.setItem('access_token', token);
          patchState(store, { isLoading: true });

          return http.get<User>('/api/v1/auth/me').pipe(
            tapResponse({
              next: (user) => {
                patchState(store, { user, isLoading: false, error: null });
                localStorage.setItem('auth_user', JSON.stringify(user));
                router.navigate(['/app']);
              },
              error: () => {
                patchState(store, {
                  isLoading: false,
                  error: 'Failed to fetch user details',
                });
                router.navigate(['/login']);
              },
            })
          );
        })
      ),

      logout: rxMethod<void>(
        switchMap(() => {
          return http.post('/api/v1/auth/logout', {}).pipe(
            tapResponse({
              next: () => {
                localStorage.removeItem('access_token');
                localStorage.removeItem('auth_user');
                patchState(store, { user: null, error: null });
                router.navigate(['/login']);
              },
              error: () => {
                // Even on error, clear local state
                localStorage.removeItem('access_token');
                localStorage.removeItem('auth_user');
                patchState(store, { user: null });
                router.navigate(['/login']);
              },
            })
          );
        })
      ),

      clearError(): void {
        patchState(store, { error: null });
      },
    };
  }),
  withHooks({
    onInit(store) {
      store.initializeAuth();
    },
  })
);