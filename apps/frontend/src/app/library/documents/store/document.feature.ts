import { createFeature, createSelector } from '@ngrx/store';
import { documentReducer } from './document.reducer';
import {
  AsyncDataItemState,
  queryAsyncState,
  unwrapAsyncDataItem,
} from '../../../core/utils/async-data-item';

export const documentFeature = createFeature({
  name: 'document',
  reducer: documentReducer,
  extraSelectors: ({ selectDocuments, selectPagination }) => ({
    // Document list selectors
    selectDocumentList: createSelector(
      selectDocuments,
      (documents) => unwrapAsyncDataItem(documents) || []
    ),

    selectDocumentsLoading: createSelector(
      selectDocuments,
      (documents) => documents.state === AsyncDataItemState.LOADING
    ),

    selectDocumentsError: createSelector(
      selectDocuments,
      (documents) => documents.error
    ),

    selectDocumentsEmpty: createSelector(selectDocuments, (asyncDocuments) => {
      const documentsState = queryAsyncState(asyncDocuments);
      const documents = unwrapAsyncDataItem(asyncDocuments);
      return documentsState.isLoaded && documents.length === 0;
    }),

    // Pagination selectors
    selectHasMore: createSelector(
      selectPagination,
      (pagination) => pagination.hasMore
    ),

    selectDocumentTotal: createSelector(
      selectPagination,
      (pagination) => pagination.total
    ),
  }),
});
