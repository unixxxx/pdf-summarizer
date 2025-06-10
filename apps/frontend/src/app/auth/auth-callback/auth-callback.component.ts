import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { AuthStore } from '../auth.store';

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
export class AuthCallbackComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private authStore = inject(AuthStore);

  ngOnInit() {
    // Check URL fragment first (for hash-based tokens)
    const fragment = window.location.hash.substring(1);
    const fragmentParams = new URLSearchParams(fragment);
    const fragmentToken = fragmentParams.get('token');

    if (fragmentToken) {
      this.authStore.handleCallback(fragmentToken);
      return;
    }

    // Check query params
    this.route.queryParams.subscribe((params) => {
      const token = params['token'];
      const error = params['error'];

      if (token) {
        this.authStore.handleCallback(token);
      } else if (error) {
        // Redirect to login with error
        window.location.href = '/login?error=' + error;
      } else {
        // No token received - redirect to login
        window.location.href = '/login';
      }
    });
  }
}
