import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute } from '@angular/router';
import { Store } from '@ngrx/store';
import { AuthActions } from '../../store/auth.actions';

@Component({
  selector: 'app-auth-callback',
  standalone: true,
  template: `
    <div class="min-h-screen bg-gray-50 flex items-center justify-center">
      <div class="text-center">
        <div
          class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"
        ></div>
        <p class="mt-4 text-gray-600">Signing you in...</p>
      </div>
    </div>
  `,
  styles: [
    `
      @keyframes spin {
        to {
          transform: rotate(360deg);
        }
      }
      .animate-spin {
        animation: spin 1s linear infinite;
      }
    `,
  ],
})
export class AuthCallback implements OnInit {
  private route = inject(ActivatedRoute);
  private store = inject(Store);
  private destroyRef = inject(DestroyRef);

  ngOnInit() {
    // Check URL fragment first (for hash-based tokens)
    const fragment = window.location.hash.substring(1);
    const fragmentParams = new URLSearchParams(fragment);
    const fragmentToken = fragmentParams.get('token');

    if (fragmentToken) {
      this.store.dispatch(
        AuthActions.loginHandleCallbackCommand({ token: fragmentToken })
      );
      return;
    }

    // Check query params
    this.route.queryParams
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((params) => {
        const token = params['token'];
        const error = params['error'];

        if (token) {
          this.store.dispatch(
            AuthActions.loginHandleCallbackCommand({ token })
          );
        } else if (error) {
          window.location.href = '/login?error=' + error;
        } else {
          window.location.href = '/login';
        }
      });
  }
}
