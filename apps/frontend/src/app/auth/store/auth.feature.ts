import { createFeature, createSelector } from '@ngrx/store';
import { authReducer } from './auth.reducer';
import {
  queryAsyncState,
  unwrapAsyncDataItem,
} from '../../core/utils/async-data-item';

export const authFeature = createFeature({
  name: 'auth',
  reducer: authReducer,
  extraSelectors: ({ selectUser }) => ({
    isAuthenticated: createSelector(selectUser, (asyncUser) => {
      const state = queryAsyncState(asyncUser);
      const user = unwrapAsyncDataItem(asyncUser);

      return state.isLoaded && Boolean(user);
    }),
  }),
});
