import {
  Component,
  signal,
  computed,
  viewChild,
  ElementRef,
  inject,
  OnInit,
  effect,
  input,
} from '@angular/core';

import { FormsModule } from '@angular/forms';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

export interface ChipItem {
  id: string | undefined;
  name: string;
  color: string | undefined;
}

@Component({
  selector: 'app-chip-input',
  standalone: true,
  imports: [FormsModule],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: ChipInput,
      multi: true,
    },
  ],
  template: `
    <div class="w-full">
      <!-- Input container -->
      <div
        class="flex flex-wrap gap-2 p-2 border border-border rounded-lg bg-background min-h-[42px] cursor-text"
        (click)="focusInput()"
        [class.ring-2]="isFocused()"
        [class.ring-primary-500]="isFocused()"
        [class.border-primary-500]="isFocused()"
        role="button"
        tabindex="0"
        (keydown.space)="focusInput()"
        (keydown.enter)="focusInput()"
      >
        <!-- Selected chips -->
        @for (item of selectedItems(); track item.id) {
        <div
          class="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium animate-in fade-in duration-200"
          [style.background-color]="item.color + '20'"
          [style.color]="item.color"
        >
          <span>{{ item.name }}</span>
          <button
            type="button"
            (click)="removeChip(item); $event.stopPropagation()"
            class="ml-1 hover:bg-black/10 dark:hover:bg-white/10 rounded-full p-0.5 transition-colors"
            [attr.aria-label]="'Remove ' + item.name"
          >
            <svg
              class="w-3 h-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
        }

        <!-- Input field -->
        <input
          #inputElement
          type="text"
          [(ngModel)]="inputValue"
          (focus)="onFocus()"
          (blur)="onBlur()"
          (keydown)="onKeyDown($event)"
          [placeholder]="selectedItems().length === 0 ? placeholder() : ''"
          class="flex-1 min-w-[120px] bg-transparent outline-none text-sm text-foreground placeholder-muted-foreground"
          autocomplete="off"
        />
      </div>

      <!-- Autocomplete dropdown -->
      @if (showDropdown() && filteredSuggestions().length > 0) {
      <div
        class="absolute z-50 mt-1 w-full max-h-60 overflow-auto rounded-lg border border-border bg-background shadow-lg animate-in fade-in slide-in-from-top-1 duration-200"
        (mousedown)="$event.preventDefault()"
      >
        @for (suggestion of filteredSuggestions(); track suggestion.id; let i =
        $index) {
        <button
          type="button"
          (click)="selectSuggestion(suggestion)"
          (mouseenter)="highlightedIndex.set(i)"
          [class.bg-muted]="highlightedIndex() === i"
          class="w-full text-left px-3 py-2 text-sm hover:bg-muted transition-colors flex items-center gap-2"
        >
          <span
            class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
            [style.background-color]="suggestion.color + '20'"
            [style.color]="suggestion.color"
          >
            {{ suggestion.name }}
          </span>
        </button>
        }
      </div>
      }

      <!-- Create new option -->
      @if (showDropdown() && inputValue.trim() && !exactMatch()) {
      <div
        class="absolute z-50 mt-1 w-full rounded-lg border border-border bg-background shadow-lg animate-in fade-in slide-in-from-top-1 duration-200"
        (mousedown)="$event.preventDefault()"
      >
        <button
          type="button"
          (click)="createNew()"
          class="w-full text-left px-3 py-2 text-sm hover:bg-muted transition-colors flex items-center gap-2"
        >
          <svg
            class="w-4 h-4 text-primary-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 4v16m8-8H4"
            />
          </svg>
          <span
            >Create "<strong>{{ inputValue.trim() }}</strong
            >"</span
          >
        </button>
      </div>
      }
    </div>
  `,
  styles: [
    `
      :host {
        display: block;
        position: relative;
      }
    `,
  ],
})
export class ChipInput implements ControlValueAccessor, OnInit {
  inputElement =
    viewChild.required<ElementRef<HTMLInputElement>>('inputElement');

  placeholder = input('Add tags...');
  suggestions = input<ChipItem[]>([]);

  inputValue = '';
  selectedItems = signal<ChipItem[]>([]);
  isFocused = signal(false);
  showDropdown = signal(false);
  highlightedIndex = signal(-1);

  // ControlValueAccessor
  onChange: (value: ChipItem[]) => void = () => {
    // Implemented in registerOnChange
  };
  onTouched: () => void = () => {
    // Implemented in registerOnTouched
  };

  filteredSuggestions = computed(() => {
    const searchTerm = this.inputValue.toLowerCase().trim();
    const selected = new Set(this.selectedItems().map((item) => item.id));

    return this.suggestions()
      .filter(
        (item) =>
          !selected.has(item.id) &&
          (searchTerm === '' || item.name.toLowerCase().includes(searchTerm))
      )
      .slice(0, 10); // Limit to 10 suggestions
  });

  exactMatch = computed(() => {
    const searchTerm = this.inputValue.toLowerCase().trim();
    return this.suggestions().some(
      (item) => item.name.toLowerCase() === searchTerm
    );
  });

  constructor() {
    // Update value when selected items change
    effect(() => {
      this.onChange(this.selectedItems());
    });
  }

  ngOnInit() {
    // Close dropdown on outside click
    document.addEventListener('click', (event) => {
      const target = event.target as HTMLElement;
      if (!this.elementRef.nativeElement.contains(target)) {
        this.showDropdown.set(false);
      }
    });
  }

  private elementRef = inject(ElementRef);

  writeValue(value: ChipItem[]): void {
    if (value && Array.isArray(value)) {
      this.selectedItems.set(value);
    } else {
      this.selectedItems.set([]);
    }
  }

  registerOnChange(fn: (value: ChipItem[]) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState?(isDisabled: boolean): void {
    const element = this.inputElement();
    if (element) {
      element.nativeElement.disabled = isDisabled;
    }
  }

  focusInput() {
    this.inputElement().nativeElement.focus();
  }

  onFocus() {
    this.isFocused.set(true);
    this.showDropdown.set(true);
    this.highlightedIndex.set(-1);
  }

  onBlur() {
    this.isFocused.set(false);
    // Delay hiding dropdown to allow click events
    setTimeout(() => {
      this.showDropdown.set(false);
    }, 200);
  }

  onKeyDown(event: KeyboardEvent) {
    const suggestions = this.filteredSuggestions();

    switch (event.key) {
      case 'Enter':
        event.preventDefault();
        if (
          this.highlightedIndex() >= 0 &&
          this.highlightedIndex() < suggestions.length
        ) {
          this.selectSuggestion(suggestions[this.highlightedIndex()]);
        } else if (this.inputValue.trim() && !this.exactMatch()) {
          this.createNew();
        }
        break;

      case 'ArrowDown':
        event.preventDefault();
        this.highlightedIndex.update((i) =>
          Math.min(i + 1, suggestions.length - 1)
        );
        break;

      case 'ArrowUp':
        event.preventDefault();
        this.highlightedIndex.update((i) => Math.max(i - 1, -1));
        break;

      case 'Backspace':
        if (this.inputValue === '' && this.selectedItems().length > 0) {
          const items = this.selectedItems();
          this.removeChip(items[items.length - 1]);
        }
        break;

      case 'Escape':
        this.showDropdown.set(false);
        this.highlightedIndex.set(-1);
        break;
    }
  }

  selectSuggestion(item: ChipItem) {
    this.selectedItems.update((items) => [...items, item]);
    this.inputValue = '';
    this.highlightedIndex.set(-1);
    // Keep dropdown open and maintain focus
    this.showDropdown.set(true);
    this.focusInput();
  }

  removeChip(item: ChipItem) {
    this.selectedItems.update((items) => items.filter((i) => i.id !== item.id));
  }

  createNew() {
    const name = this.inputValue.trim();
    if (name) {
      // Create a new ChipItem with a temporary ID
      const newItem: ChipItem = {
        id: undefined,
        name: name,
        color: this.generateColor(name),
      };
      this.selectedItems.update((items) => [...items, newItem]);
      this.inputValue = '';
      this.highlightedIndex.set(-1);
      // Keep dropdown open and maintain focus
      this.showDropdown.set(true);
      this.focusInput();
    }
  }

  private generateColor(name: string): string {
    // Generate a consistent color based on the name
    const colors = [
      '#3B82F6', // blue
      '#10B981', // emerald
      '#8B5CF6', // violet
      '#F59E0B', // amber
      '#EF4444', // red
      '#EC4899', // pink
      '#6366F1', // indigo
      '#14B8A6', // teal
    ];
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
  }
}
