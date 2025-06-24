export interface AsyncDataItem<T> {
  data: T;
  state: AsyncDataItemState;
  error: string;
}

export enum AsyncDataItemState {
  LOADING = 'loading',
  LOADED = 'loaded',
  ERROR = 'error',
  IDLE = 'idle',
}

export interface QueryAsyncState {
  isError: boolean;
  isLoading: boolean;
  isLoaded: boolean;
  isIdle: boolean;
}

export function wrapAsAsyncDataItem<T>(
  data: T,
  state = AsyncDataItemState.LOADING,
  error = ''
): AsyncDataItem<T> {
  return { data, state, error };
}

export function unwrapAsyncDataItem<T>(asyncDataItem: AsyncDataItem<T>): T {
  return asyncDataItem.data;
}

export function queryAsyncState(
  asyncDataItem: AsyncDataItem<unknown>
): QueryAsyncState {
  return {
    isError: asyncDataItem.state === AsyncDataItemState.ERROR,
    isLoading: asyncDataItem.state === AsyncDataItemState.LOADING,
    isLoaded: asyncDataItem.state === AsyncDataItemState.LOADED,
    isIdle: asyncDataItem.state === AsyncDataItemState.IDLE,
  };
}

export function getAsyncState(
  asyncDataItem: AsyncDataItem<unknown>
): AsyncDataItemState {
  return asyncDataItem.state;
}
