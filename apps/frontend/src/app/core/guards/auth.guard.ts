import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { authFeature } from '../../auth/store/auth.feature';

export const authGuard = () => {
  const store = inject(Store);
  const router = inject(Router);

  if (store.selectSignal(authFeature.isAuthenticated)()) {
    return true;
  }

  return router.parseUrl('/login');
};
