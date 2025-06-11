import { Component, ChangeDetectionStrategy, input, output, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Tag } from '../tag.model';

@Component({
  selector: 'app-tag',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span
      [class]="getClasses()"
      [style.background-color]="backgroundColor()"
      [style.color]="textColor()"
      [style.border-color]="borderColor()"
      (click)="handleClick($event)"
      [class.cursor-pointer]="clickable()"
      [attr.role]="clickable() ? 'button' : null"
      [attr.tabindex]="clickable() ? 0 : null"
      (keydown.enter)="handleClick($event)"
      (keydown.space)="handleClick($event)"
    >
      {{ tag().name }}
      <ng-content></ng-content>
    </span>
  `,
})
export class TagComponent {
  // Input signals
  tag = input.required<Tag>();
  variant = input<'default' | 'filter' | 'small'>('default');
  selected = input(false);
  clickable = input(false);
  
  // Output signals
  tagClick = output<Tag>();

  // Computed properties
  backgroundColor = computed(() => {
    const tagValue = this.tag();
    const variantValue = this.variant();
    const selectedValue = this.selected();
    
    if (variantValue === 'filter' && selectedValue) {
      return tagValue.color + '20'; // 20% opacity
    }
    if (variantValue === 'default') {
      return tagValue.color + '20'; // 20% opacity
    }
    return 'transparent';
  });

  textColor = computed(() => {
    const tagValue = this.tag();
    const variantValue = this.variant();
    const selectedValue = this.selected();
    
    if (variantValue === 'filter' && selectedValue) {
      return tagValue.color;
    }
    if (variantValue === 'default') {
      return tagValue.color;
    }
    return 'currentColor';
  });

  borderColor = computed(() => {
    const tagValue = this.tag();
    const variantValue = this.variant();
    const selectedValue = this.selected();
    
    if (variantValue === 'filter') {
      return selectedValue ? tagValue.color : undefined;
    }
    return undefined;
  });

  getClasses(): string {
    const baseClasses = 'inline-flex items-center font-medium rounded-full transition-colors';
    
    const sizeClasses = {
      default: 'px-2 py-0.5 text-xs',
      filter: 'px-3 py-1 text-sm',
      small: 'px-1.5 py-0.5 text-xs',
    };

    const variantClasses = {
      default: '',
      filter: 'border hover:bg-muted',
      small: '',
    };

    const selectedClasses = this.selected() ? 'bg-primary-100 dark:bg-primary-900' : '';

    return `${baseClasses} ${sizeClasses[this.variant()]} ${variantClasses[this.variant()]} ${selectedClasses}`;
  }

  handleClick(event: Event) {
    if (this.clickable()) {
      event.stopPropagation();
      this.tagClick.emit(this.tag());
    }
  }
}