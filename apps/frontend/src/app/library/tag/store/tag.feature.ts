import { createFeature } from '@ngrx/store';
import { tagReducer } from './tag.reducers';

export const tagFeature = createFeature({
  name: 'tag',
  reducer: tagReducer,
});