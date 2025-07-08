import { AsyncDataItem } from '../../../../core/utils/async-data-item';
import { DocumentListItem } from './document';
import { PaginationState } from './pagination';
import { DocumentSearchCriteria } from '../../dtos/document-search-criteria';

export interface DocumentState {
  documents: AsyncDataItem<DocumentListItem[]>;
  pagination: PaginationState;
  currentCriteria: DocumentSearchCriteria | undefined;
}
