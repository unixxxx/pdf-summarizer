import {
  Component,
  inject,
  ChangeDetectionStrategy,
  signal,
  output,
} from '@angular/core';

import { FormsModule } from '@angular/forms';
import { UIStore } from '../../../shared/ui.store';

@Component({
  selector: 'app-document-search',
  standalone: true,
  imports: [FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="p-4">
      <!-- Search and Upload Row -->
      <div class="flex gap-3">
        <!-- Folder Menu Button (Mobile Only) -->
        <button
          (click)="uiStore.toggleSidebar()"
          class="sm:hidden p-2 bg-background border border-border rounded-lg hover:bg-muted transition-colors"
          aria-label="Toggle folders"
        >
          <svg
            class="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 5l7 7-7 7M5 5l7 7-7 7"
            />
          </svg>
        </button>

        <!-- Search Input -->
        <div class="relative flex-1">
          <svg
            class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            [ngModel]="searchQuery()"
            (ngModelChange)="updateSearch($event)"
            placeholder="Search documents..."
            class="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        <!-- Upload Button -->
        <button
          (click)="uploadClick.emit()"
          class="px-4 sm:px-6 py-2 bg-gradient-to-r from-primary-600 to-accent-600 text-white rounded-lg font-medium hover:shadow-lg transform hover:scale-[1.02] transition-all flex items-center gap-2"
        >
          <svg
            class="w-5 h-5"
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
          <span class="hidden sm:inline">Upload</span>
        </button>
      </div>

      <!-- Active Filters Summary -->
      @if (isSearching()) {
      <div class="mt-3 flex items-center gap-2">
        <span class="text-sm text-muted-foreground">Active filters:</span>
        @if (searchQuery()) {
        <span class="px-2 py-1 text-xs bg-muted rounded-full">
          Search: "{{ searchQuery() }}"
        </span>
        }
        <button
          (click)="clearFilters()"
          class="ml-auto text-sm text-primary-600 hover:text-primary-700"
        >
          Clear all
        </button>
      </div>
      }
    </div>
  `,
})
export class DocumentSearch {
  uploadClick = output<void>();
  searchChange = output<string>();

  protected uiStore = inject(UIStore);

  // Local state
  protected searchQuery = signal('');
  protected isSearching = signal(false);

  updateSearch(query: string) {
    this.searchQuery.set(query);
    this.isSearching.set(query.length > 0);
    this.searchChange.emit(query);
  }

  clearFilters() {
    this.searchQuery.set('');
    this.isSearching.set(false);
    this.searchChange.emit('');
  }
}
