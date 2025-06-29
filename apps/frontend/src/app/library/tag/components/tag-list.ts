import {
  Component,
  ChangeDetectionStrategy,
  input,
  output,
  computed,
} from '@angular/core';

import { Tag as TagComponent } from './tag';
import { Tag as TagModel } from '../store/state/tag';

@Component({
  selector: 'app-tag-list',
  standalone: true,
  imports: [TagComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="flex flex-wrap" [class]="gapClass()">
      @for (tag of tags(); track tag.id) {
      <app-tag
        [tag]="tag"
        [variant]="variant()"
        [clickable]="clickable()"
        (tagClick)="onTagClick($event)"
      >
      </app-tag>
      }
    </div>
  `,
})
export class TagList {
  // Input signals
  tags = input<TagModel[]>([]);
  variant = input<'default' | 'filter' | 'small'>('default');
  clickable = input(false);
  gapSize = input<'small' | 'medium' | 'large'>('medium');

  // Output signals
  tagClick = output<TagModel>();

  // Computed properties
  gapClass = computed(() => {
    const gapClasses = {
      small: 'gap-1',
      medium: 'gap-2',
      large: 'gap-3',
    };
    return gapClasses[this.gapSize()];
  });

  onTagClick(tag: TagModel) {
    this.tagClick.emit(tag);
  }
}
