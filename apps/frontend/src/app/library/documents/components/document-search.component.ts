import { Component, inject, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LibraryStore } from '../../library.store';
import { TagFilterComponent } from '../../tags/components/tag-filter.component';

@Component({
  selector: 'app-document-search',
  standalone: true,
  imports: [CommonModule, FormsModule, TagFilterComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="p-4 border-b border-border">
      <!-- Search Input -->
      <div class="relative">
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

      <!-- Tag Filters -->
      @if (libraryStore.tags().length > 0) {
        <div class="mt-3">
          <app-tag-filter
            [tags]="libraryStore.tags()"
            [selectedTags]="libraryStore.selectedTags()"
            (tagToggled)="toggleTag($event)"
          />
        </div>
      }

      <!-- Active Filters Summary -->
      @if (libraryStore.documentsIsSearching()) {
        <div class="mt-3 flex items-center gap-2">
          <span class="text-sm text-muted-foreground">Active filters:</span>
          @if (libraryStore.searchQuery()) {
            <span class="px-2 py-1 text-xs bg-muted rounded-full">
              Search: "{{ libraryStore.searchQuery() }}"
            </span>
          }
          @if (libraryStore.selectedTags().length > 0) {
            <span class="px-2 py-1 text-xs bg-muted rounded-full">
              {{ libraryStore.selectedTags().length }} tag(s)
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
  protected libraryStore = inject(LibraryStore);

  updateSearch(query: string) {
    this.libraryStore.setSearchQuery(query);
    this.libraryStore.loadDocuments();
  }

  toggleTag(tagSlug: string) {
    this.libraryStore.toggleTag(tagSlug);
    this.libraryStore.loadDocuments();
  }

  clearFilters() {
    this.libraryStore.clearFilters();
    this.libraryStore.loadDocuments();
  }
}