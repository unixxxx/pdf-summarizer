import { Component, ChangeDetectionStrategy, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TagComponent } from './tag.component';
import { Tag } from '../tag.model';

@Component({
  selector: 'app-tag-filter',
  standalone: true,
  imports: [CommonModule, TagComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="flex flex-wrap gap-2">
      @for (tag of tags(); track tag.id) {
        <app-tag
          [tag]="tag"
          variant="filter"
          [selected]="isSelected(tag)"
          [clickable]="true"
          (tagClick)="onTagClick($event)"
        >
          @if (tag.documentCount) {
            <span class="ml-1 text-xs opacity-60">({{ tag.documentCount }})</span>
          }
        </app-tag>
      }
    </div>
  `,
})
export class TagFilterComponent {
  // Input signals
  tags = input<Tag[]>([]);
  selectedTags = input<string[]>([]);
  
  // Output signals
  tagToggled = output<string>();

  isSelected(tag: Tag): boolean {
    return this.selectedTags().includes(tag.slug);
  }

  onTagClick(tag: Tag) {
    this.tagToggled.emit(tag.slug);
  }
}