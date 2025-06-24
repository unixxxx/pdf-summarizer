import { AsyncDataItem } from '../../../../core/utils/async-data-item';
import { Tag } from './tag';

export interface TagState {
  tags: AsyncDataItem<Tag[]>;
}
