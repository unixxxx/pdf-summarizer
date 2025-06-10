import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { AuthStore } from './auth.store';

export const authGuard = () => {
  const authStore = inject(AuthStore);
  const router = inject(Router);

  if (authStore.isAuthenticated()) {
    return true;
  }

  return router.parseUrl('/login');
};
