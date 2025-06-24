import { Pipe, PipeTransform } from '@angular/core';
import { AsyncDataItem, unwrapAsyncDataItem } from '../utils/async-data-item';

@Pipe({
  name: 'unwrapAsyncData',
  standalone: true,
})
export class UnwrapAsyncDataPipe implements PipeTransform {
  transform<T>(value: AsyncDataItem<T>): T {
    return unwrapAsyncDataItem(value);
  }
}
