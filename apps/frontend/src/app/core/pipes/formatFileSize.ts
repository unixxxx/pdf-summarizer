import { Pipe, PipeTransform } from '@angular/core';
import { formatFileSize } from '../utils/file-size.formatter';

@Pipe({
  name: 'formatFileSize',
  standalone: true,
})
export class FormatFileSizePipe implements PipeTransform {
  transform(bytes: number): string {
    return formatFileSize(bytes);
  }
}
