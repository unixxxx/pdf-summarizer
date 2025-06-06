import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { AuthService } from '../auth.service';

@Component({
  selector: 'app-auth-callback',
  standalone: true,
  template: `
    <div class="min-h-screen bg-gray-50 flex items-center justify-center">
      <div class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-4 text-gray-600">Signing you in...</p>
      </div>
    </div>
  `,
  styles: [`
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    .animate-spin {
      animation: spin 1s linear infinite;
    }
  `]
})
export class AuthCallbackComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private authService = inject(AuthService);
  
  ngOnInit() {
    // Check URL fragment first (for hash-based tokens)
    const fragment = window.location.hash.substring(1);
    const fragmentParams = new URLSearchParams(fragment);
    const fragmentToken = fragmentParams.get('token');
    
    if (fragmentToken) {
      console.log('Token found in fragment');
      this.authService.handleCallback(fragmentToken);
      return;
    }
    
    // Check query params
    this.route.queryParams.subscribe(params => {
      console.log('Query params:', params);
      const token = params['token'];
      const error = params['error'];
      
      if (token) {
        console.log('Token found in query params');
        this.authService.handleCallback(token);
      } else if (error) {
        console.error('Authentication error:', error);
        // Redirect to login with error
        window.location.href = '/login?error=' + error;
      } else {
        console.error('No token received in query params or fragment');
        console.log('Full URL:', window.location.href);
        window.location.href = '/login';
      }
    });
  }
}