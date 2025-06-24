import { createReducer, on } from '@ngrx/store';
import { TagState } from './state/tag-state';
import { TagActions } from './tag.actions';
import {
  AsyncDataItemState,
  wrapAsAsyncDataItem,
} from '../../../core/utils/async-data-item';
import { toTag } from './state/tag';

const initialState: TagState = {
  tags: wrapAsAsyncDataItem([], AsyncDataItemState.IDLE),
};

export const tagReducer = createReducer<TagState>(
  initialState,
  on(TagActions.fetchTagsCommand, (state) => ({
    ...state,
    tags: wrapAsAsyncDataItem(state.tags.data, AsyncDataItemState.LOADING),
  })),
  on(TagActions.fetchTagsSuccessEvent, (state, { tags }) => ({
    ...state,
    tags: wrapAsAsyncDataItem(tags.map(toTag), AsyncDataItemState.LOADED),
  })),
  on(TagActions.fetchTagsFailureEvent, (state, { error }) => ({
    ...state,
    tags: wrapAsAsyncDataItem(state.tags.data, AsyncDataItemState.ERROR, error),
  }))
);
