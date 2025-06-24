import { Pipe, PipeTransform } from '@angular/core';
import {
  AsyncDataItem,
  queryAsyncState,
  QueryAsyncState,
} from '../utils/async-data-item';

@Pipe({
  name: 'queryAsyncState',
  standalone: true,
})
export class QueryAsyncStatePipe implements PipeTransform {
  transform<T>(value: AsyncDataItem<T>): QueryAsyncState {
    return queryAsyncState(value);
  }
}
