import { Component, ChangeDetectionStrategy, input, output, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TagComponent } from './tag.component';
import { Tag } from '../tag.model';

@Component({
  selector: 'app-tag-list',
  standalone: true,
  imports: [CommonModule, TagComponent],
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
          @if (showCount() && tag.documentCount) {
            <span class="ml-1 text-xs opacity-60">({{ tag.documentCount }})</span>
          }
        </app-tag>
      }
    </div>
  `,
})
export class TagListComponent {
  // Input signals
  tags = input<Tag[]>([]);
  variant = input<'default' | 'filter' | 'small'>('default');
  clickable = input(false);
  showCount = input(false);
  gapSize = input<'small' | 'medium' | 'large'>('medium');
  
  // Output signals
  tagClick = output<Tag>();

  // Computed properties
  gapClass = computed(() => {
    const gapClasses = {
      small: 'gap-1',
      medium: 'gap-2',
      large: 'gap-3',
    };
    return gapClasses[this.gapSize()];
  });

  onTagClick(tag: Tag) {
    this.tagClick.emit(tag);
  }
}