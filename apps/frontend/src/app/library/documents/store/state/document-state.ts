import { AsyncDataItem } from '../../../../core/utils/async-data-item';
import { DocumentListItem } from './document';
import { PaginationState } from './pagination';

export interface DocumentState {
  documents: AsyncDataItem<DocumentListItem[]>;
  pagination: PaginationState;
}
