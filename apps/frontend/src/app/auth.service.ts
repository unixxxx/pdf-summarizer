import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap, catchError, of } from 'rxjs';

export interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);
  
  private currentUserSignal = signal<User | null>(null);
  currentUser = this.currentUserSignal.asReadonly();
  
  constructor() {
    this.loadUser();
  }
  
  loadUser(): void {
    const token = localStorage.getItem('access_token');
    console.log('Loading user, token exists:', !!token);
    
    if (token) {
      this.http.get<User>('/api/v1/auth/me').subscribe({
        next: (user) => {
          console.log('User loaded:', user);
          this.currentUserSignal.set(user);
        },
        error: (error) => {
          console.error('Failed to load user:', error);
          localStorage.removeItem('access_token');
          this.currentUserSignal.set(null);
        }
      });
    }
  }
  
  login(provider: 'google' | 'github'): void {
    // Pass the redirect URL to ensure we come back to the auth callback
    const redirectUrl = `${window.location.origin}/auth/callback`;
    this.http.get<{ authorization_url: string }>(`/api/v1/auth/login/${provider}?redirect_url=${encodeURIComponent(redirectUrl)}`).subscribe({
      next: (response) => {
        window.location.href = response.authorization_url;
      },
      error: (error) => {
        console.error('Login failed:', error);
      }
    });
  }
  
  handleCallback(token: string): void {
    console.log('Handling callback with token:', token);
    localStorage.setItem('access_token', token);
    this.loadUser();
    // Use a small delay to ensure the user is loaded before navigation
    setTimeout(() => {
      this.router.navigate(['/app']);
    }, 100);
  }
  
  logout(): Observable<void> {
    return this.http.post<void>('/api/v1/auth/logout', {}).pipe(
      tap(() => {
        localStorage.removeItem('access_token');
        this.currentUserSignal.set(null);
        this.router.navigate(['/login']);
      }),
      catchError(() => {
        localStorage.removeItem('access_token');
        this.currentUserSignal.set(null);
        this.router.navigate(['/login']);
        return of(undefined);
      })
    );
  }
  
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  }
}