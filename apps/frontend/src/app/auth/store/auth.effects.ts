import { inject, Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { AuthActions } from './auth.actions';
import { switchMap, tap } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { mapResponse } from '@ngrx/operators';
import { User } from '../../core/interfaces/user.interface';
import { Router } from '@angular/router';

@Injectable()
export class AuthEffects {
  private readonly actions$ = inject(Actions);
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  login$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.loginCommand),
      switchMap((action) =>
        this.http
          .get<{ authorization_url: string; state: string }>(
            `/api/v1/auth/login/${action.provider}`
          )
          .pipe(
            mapResponse({
              next: (response) =>
                AuthActions.loginRedirectToProviderCommand({
                  authorization_url: response.authorization_url,
                  state: response.state,
                }),
              error: (error: Error) =>
                AuthActions.loginFailureEvent({ error: error.message }),
            })
          )
      )
    )
  );

  loginRedirect$ = createEffect(
    () =>
      this.actions$.pipe(
        ofType(AuthActions.loginRedirectToProviderCommand),
        tap((action) => {
          window.location.href = action.authorization_url;
        })
      ),
    { dispatch: false }
  );

  handleCallback$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.loginHandleCallbackCommand),
      tap((action) => {
        localStorage.setItem('access_token', action.token);
      }),
      switchMap(() =>
        this.http.get<User>('/api/v1/auth/me').pipe(
          mapResponse({
            next: (user) => AuthActions.loginSuccessEvent({ user }),
            error: (error: Error) =>
              AuthActions.loginFailureEvent({ error: error.message }),
          })
        )
      )
    )
  );

  loginSuccess$ = createEffect(
    () =>
      this.actions$.pipe(
        ofType(AuthActions.loginSuccessEvent),
        tap((action) => {
          localStorage.setItem('auth_user', JSON.stringify(action.user));
          this.router.navigate(['/']);
        })
      ),
    { dispatch: false }
  );

  logout$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.logoutCommand),
      tap(() => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('auth_user');
      }),
      mapResponse({
        next: () => AuthActions.logoutSuccessEvent(),
        error: (error: Error) =>
          AuthActions.logoutFailureEvent({ error: error.message }),
      })
    )
  );

  logoutSuccess$ = createEffect(
    () =>
      this.actions$.pipe(
        ofType(AuthActions.logoutSuccessEvent),
        tap(() => {
          this.router.navigate(['/login']);
        })
      ),
    { dispatch: false }
  );

  refreshTokenFailure$ = createEffect(
    () =>
      this.actions$.pipe(
        ofType(AuthActions.refreshTokenFailureEvent),
        tap(() => {
          // Redirect to login on refresh failure
          this.router.navigate(['/login']);
        })
      ),
    { dispatch: false }
  );
}
