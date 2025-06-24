import { createActionGroup, emptyProps, props } from '@ngrx/store';
import { User } from '../../core/interfaces/user.interface';

export const AuthActions = createActionGroup({
  source: 'Auth',
  events: {
    'Login command': props<{ provider: 'google' | 'github' }>(),
    'Login redirect to provider command': props<{
      authorization_url: string;
      state: string;
    }>(),
    'Login handle callback command': props<{ token: string }>(),
    'Login success event': props<{ user: User }>(),
    'Login failure event': props<{ error: string }>(),

    'Logout command': emptyProps(),
    'Logout success event': emptyProps(),
    'Logout failure event': props<{ error: string }>(),
  },
});
