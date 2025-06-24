import { Component, OnInit, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

@Component({
  selector: 'app-auth-error',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="min-h-screen bg-gray-50 flex items-center justify-center">
      <div class="max-w-md w-full bg-white shadow rounded-lg p-8 text-center">
        <div
          class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4"
        >
          <svg
            class="w-8 h-8 text-red-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            ></path>
          </svg>
        </div>

        <h1 class="text-2xl font-bold text-gray-900 mb-2">
          Authentication Failed
        </h1>

        <p class="text-gray-600 mb-6">
          {{ errorMessage }}
        </p>

        <div class="space-y-3">
          <a
            routerLink="/login"
            class="block w-full bg-blue-600 text-white rounded-md px-4 py-2 hover:bg-blue-700 transition-colors"
          >
            Back to Login
          </a>

          <p class="text-sm text-gray-500">
            If this problem persists, please contact support.
          </p>
        </div>
      </div>
    </div>
  `,
})
export class AuthError implements OnInit {
  private route = inject(ActivatedRoute);

  errorMessage =
    'We encountered an error during authentication. Please try again.';

  ngOnInit() {
    this.route.queryParams.pipe(takeUntilDestroyed()).subscribe((params) => {
      const error = params['error'];

      // Map error codes to user-friendly messages
      switch (error) {
        case 'authentication_failed':
          this.errorMessage =
            'Authentication failed. Please check your credentials and try again.';
          break;
        case 'provider_error':
          this.errorMessage =
            'The authentication provider encountered an error. Please try again later.';
          break;
        case 'invalid_state':
          this.errorMessage =
            'Invalid authentication state. Please start the login process again.';
          break;
        case 'access_denied':
          this.errorMessage =
            'Access was denied. You need to authorize the application to continue.';
          break;
        default:
          this.errorMessage =
            'An unexpected error occurred during authentication. Please try again.';
      }
    });
  }
}
