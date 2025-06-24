import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideStoreDevtools } from '@ngrx/store-devtools';
import { OverlayModule } from '@angular/cdk/overlay';
import { importProvidersFrom } from '@angular/core';

import { routes } from './app.routes';
import { provideState, provideStore } from '@ngrx/store';
import { authFeature } from './auth/store/auth.feature';
import { provideEffects } from '@ngrx/effects';
import { AuthEffects } from './auth/store/auth.effects';
import { authInterceptor } from './core/interceptors/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor])),
    provideAnimations(),
    importProvidersFrom(OverlayModule),
    provideStore(
      {},
      {
        runtimeChecks: {
          strictActionImmutability: false,
          strictActionSerializability: false,
          strictStateSerializability: false,
          strictStateImmutability: false,
        },
      }
    ),
    provideStoreDevtools(),
    provideState(authFeature),
    provideEffects(AuthEffects),
  ],
};
