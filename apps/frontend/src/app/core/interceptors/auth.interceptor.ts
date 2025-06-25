import { HttpInterceptorFn, HttpErrorResponse, HttpRequest, HttpHandlerFn, HttpResponse, HttpHeaders } from '@angular/common/http';
import { inject } from '@angular/core';
import { Store } from '@ngrx/store';
import { catchError, filter, switchMap, take, throwError, BehaviorSubject } from 'rxjs';
import { AuthActions } from '../../auth/store/auth.actions';

// Track ongoing refresh
let isRefreshing = false;
const refreshTokenSubject = new BehaviorSubject<string | null>(null);

export const authInterceptor: HttpInterceptorFn = (req: HttpRequest<unknown>, next: HttpHandlerFn) => {
  const store = inject(Store);
  
  // Helper function to add auth header
  const addAuthHeader = (request: HttpRequest<unknown>, token: string) => {
    return request.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`,
      },
    });
  };

  // Get token and add to request if needed
  const token = localStorage.getItem('access_token');
  if (token && req.url.startsWith('/api') && !req.url.includes('/auth/refresh')) {
    req = addAuthHeader(req, token);
  }

  return next(req).pipe(
    catchError((error) => {
      if (error instanceof HttpErrorResponse && error.status === 401) {
        // Skip refresh for auth endpoints to prevent infinite loops
        if (req.url.includes('/auth/')) {
          return throwError(() => error);
        }

        if (!isRefreshing) {
          isRefreshing = true;
          refreshTokenSubject.next(null);
          
          // Dispatch refresh action
          store.dispatch(AuthActions.refreshTokenCommand());
          
          // Create the refresh request manually to avoid circular dependency
          const headers = new HttpHeaders({
            'Authorization': `Bearer ${token}`
          });
          const refreshReq = new HttpRequest('POST', '/api/v1/auth/refresh', {}, {
            headers
          });
          
          return next(refreshReq).pipe(
            switchMap((response) => {
              if (response instanceof HttpResponse && response.body && typeof response.body === 'object' && 'access_token' in response.body) {
                const newToken = (response.body as { access_token: string }).access_token;
                localStorage.setItem('access_token', newToken);
                isRefreshing = false;
                refreshTokenSubject.next(newToken);
                
                // Retry original request with new token
                const retryReq = addAuthHeader(req, newToken);
                return next(retryReq);
              }
              throw new Error('No access token in refresh response');
            }),
            catchError(refreshError => {
              isRefreshing = false;
              refreshTokenSubject.next(null);
              // Clear auth
              localStorage.removeItem('access_token');
              localStorage.removeItem('auth_user');
              // Dispatch failure action
              store.dispatch(AuthActions.refreshTokenFailureEvent({ error: refreshError.message }));
              return throwError(() => error);
            })
          );
        } else {
          // Wait for refresh to complete
          return refreshTokenSubject.pipe(
            filter(token => token !== null),
            take(1),
            switchMap(token => {
              const retryReq = addAuthHeader(req, token as string);
              return next(retryReq);
            })
          );
        }
      }
      
      return throwError(() => error);
    })
  );
};
