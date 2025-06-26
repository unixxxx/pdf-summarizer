import { AsyncDataItem } from '../../../../core/utils/async-data-item';
import { Archive } from './archive-type';

export interface ArchiveState {
  archive: AsyncDataItem<Archive>;
}
