import {
  Component,
  ChangeDetectionStrategy,
  input,
  computed,
} from '@angular/core';

import { Tag as TagModel } from '../store/state/tag';

@Component({
  selector: 'app-tag',
  standalone: true,
  imports: [],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span
      class="inline-flex items-center font-medium rounded-full transition-colors px-1.5 py-0.5 text-xs"
      [style.background-color]="tag().color"
      [style.color]="textColor()"
    >
      {{ tag().name }}
    </span>
  `,
})
export class Tag {
  // Input signals
  tag = input.required<TagModel>();

  textColor = computed(() => {
    const tagValue = this.tag();
    
    // Handle missing color
    if (!tagValue.color) {
      return 'currentColor';
    }

    // Calculate text color based on background color contrast
    return this.getContrastTextColor(tagValue.color);
  });

  /**
   * Determines whether to use black or white text based on the background color
   * using the WCAG contrast ratio formula
   */
  private getContrastTextColor(backgroundColor: string): string {
    // Convert hex to RGB
    const hexToRgb = (hex: string): { r: number; g: number; b: number } | null => {
      // Remove # if present
      hex = hex.replace('#', '');
      
      // Support 3-character hex
      if (hex.length === 3) {
        hex = hex.split('').map(char => char + char).join('');
      }
      
      // Validate hex
      if (!/^[0-9A-Fa-f]{6}$/.test(hex)) {
        return null;
      }
      
      const result = /^([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
      return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
      } : null;
    };

    // Calculate relative luminance
    const getLuminance = (r: number, g: number, b: number): number => {
      const [rs, gs, bs] = [r, g, b].map(c => {
        c = c / 255;
        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
      });
      return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
    };

    const rgb = hexToRgb(backgroundColor);
    if (!rgb) {
      return '#000000'; // Default to black if color parsing fails
    }

    const luminance = getLuminance(rgb.r, rgb.g, rgb.b);
    
    // Use white text for dark backgrounds, black for light backgrounds
    // Threshold of 0.5 works well for most cases
    return luminance > 0.5 ? '#000000' : '#FFFFFF';
  }
}
