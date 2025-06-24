import { createReducer, on } from '@ngrx/store';
import { AuthState } from './auth-state.interface';
import { AuthActions } from './auth.actions';
import {
  AsyncDataItemState,
  unwrapAsyncDataItem,
  wrapAsAsyncDataItem,
} from '../../core/utils/async-data-item';
import { User } from '../../core/interfaces/user.interface';

const user: User | undefined = JSON.parse(
  localStorage.getItem('auth_user') ?? 'null'
) as User | undefined;

const initialState: AuthState = {
  user: wrapAsAsyncDataItem<User | undefined>(
    user,
    user !== undefined ? AsyncDataItemState.LOADED : AsyncDataItemState.IDLE
  ),
};

export const authReducer = createReducer(
  initialState,
  on(AuthActions.loginCommand, (state) => ({
    ...state,
    user: wrapAsAsyncDataItem<User | undefined>(
      undefined,
      AsyncDataItemState.LOADING
    ),
  })),
  on(AuthActions.loginSuccessEvent, (state, { user }) => ({
    ...state,
    user: wrapAsAsyncDataItem<User | undefined>(
      user,
      AsyncDataItemState.LOADED
    ),
  })),
  on(AuthActions.loginFailureEvent, (state, { error }) => ({
    ...state,
    user: wrapAsAsyncDataItem<User | undefined>(
      undefined,
      AsyncDataItemState.ERROR,
      error
    ),
  })),
  on(AuthActions.logoutSuccessEvent, (state) => ({
    ...state,
    user: wrapAsAsyncDataItem<User | undefined>(
      undefined,
      AsyncDataItemState.IDLE
    ),
  })),
  on(AuthActions.logoutFailureEvent, (state, { error }) => ({
    ...state,
    user: wrapAsAsyncDataItem<User | undefined>(
      unwrapAsyncDataItem(state.user),
      AsyncDataItemState.ERROR,
      error
    ),
  }))
);
