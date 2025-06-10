import { Injectable, inject } from '@angular/core';
import { AuthStore } from './auth.store';

// Re-export User interface for backward compatibility
export { User } from './auth.store';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private readonly authStore = inject(AuthStore);

  // Expose store selectors for backward compatibility
  currentUser = this.authStore.user;

  loadUser(): void {
    this.authStore.loadUser(undefined);
  }

  login(provider: 'google' | 'github'): void {
    this.authStore.login(provider);
  }

  handleCallback(token: string): void {
    this.authStore.handleCallback(token);
  }

  logout(): void {
    this.authStore.logout(undefined);
  }

  isAuthenticated(): boolean {
    return this.authStore.isAuthenticated();
  }
}
