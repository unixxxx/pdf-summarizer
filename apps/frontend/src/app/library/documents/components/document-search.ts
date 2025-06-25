import {
  Component,
  inject,
  ChangeDetectionStrategy,
  Output,
  EventEmitter,
} from '@angular/core';

import { FormsModule } from '@angular/forms';
import { LibraryStore } from '../../library.store';

@Component({
  selector: 'app-document-search',
  standalone: true,
  imports: [FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="p-4">
      <!-- Search and Upload Row -->
      <div class="flex gap-3">
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
            [ngModel]="libraryStore.searchQuery()"
            (ngModelChange)="updateSearch($event)"
            placeholder="Search documents..."
            class="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        <!-- Upload Button -->
        <button
          (click)="uploadClick.emit()"
          class="px-6 py-2 bg-gradient-to-r from-primary-600 to-accent-600 text-white rounded-lg font-medium hover:shadow-lg transform hover:scale-[1.02] transition-all flex items-center gap-2"
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
          Upload
        </button>
      </div>

      <!-- Active Filters Summary -->
      @if (libraryStore.documentsIsSearching()) {
      <div class="mt-3 flex items-center gap-2">
        <span class="text-sm text-muted-foreground">Active filters:</span>
        @if (libraryStore.searchQuery()) {
        <span class="px-2 py-1 text-xs bg-muted rounded-full">
          Search: "{{ libraryStore.searchQuery() }}"
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
export class DocumentSearchComponent {
  @Output() uploadClick = new EventEmitter<void>();

  protected libraryStore = inject(LibraryStore);

  updateSearch(query: string) {
    this.libraryStore.setSearchQuery(query);
    this.libraryStore.loadDocuments();
  }

  clearFilters() {
    this.libraryStore.clearFilters();
    this.libraryStore.loadDocuments();
  }
}
