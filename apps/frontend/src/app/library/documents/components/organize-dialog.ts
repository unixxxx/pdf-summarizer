import {
  Component,
  inject,
  ChangeDetectionStrategy,
  signal,
  computed,
  input,
  OnInit,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MODAL_REF, ModalRef } from '../../../core/services/modal';
import { OrganizeSuggestion, OrganizeDialogResult } from '../dtos/organize-dialog';

@Component({
  selector: 'app-organize-dialog',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  styles: [
    `
      @keyframes scale-in {
        from {
          transform: scale(0.95);
          opacity: 0;
        }
        to {
          transform: scale(1);
          opacity: 1;
        }
      }

      .animate-scale-in {
        animation: scale-in 0.2s ease-out;
      }

      .modal-content {
        width: 100%;
        max-width: 48rem;
        max-height: 90vh;
      }

      @media (max-width: 640px) {
        .modal-content {
          max-width: 100%;
          max-height: 100vh;
          border-radius: 0;
        }
      }
    `,
  ],
  template: `
    <div
      class="modal-content bg-card border border-border rounded-xl shadow-2xl animate-scale-in w-full max-w-3xl max-h-[90vh] flex flex-col"
    >
      <!-- Header -->
      <div
        class="modal-header p-6 border-b border-border flex items-center justify-between"
      >
        <h2 class="text-xl font-semibold text-foreground">
          Organize Documents
        </h2>
        <button
          (click)="cancel()"
          class="p-2 rounded-lg hover:bg-muted transition-colors"
          aria-label="Close dialog"
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
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <!-- Body -->
      <div class="modal-body flex-1 p-6 overflow-y-auto">
        <!-- Summary Card -->
        <div class="mb-6 p-4 bg-muted/20 border border-border rounded-lg">
          <div class="flex items-start gap-3">
            <div class="p-2 bg-primary-500/10 rounded-lg">
              <svg
                class="w-5 h-5 text-primary-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <div class="flex-1">
              <p class="text-sm text-muted-foreground mb-1">
                Found
                <span class="font-medium text-foreground">{{
                  totalUnfiled()
                }}</span>
                unfiled documents,
                <span class="font-medium text-foreground">{{
                  totalWithTags()
                }}</span>
                have tags for matching.
              </p>
              @if (suggestions().length > 0) {
              <p class="text-sm font-medium text-foreground">
                {{ suggestions().length }} documents can be automatically
                organized.
              </p>
              } @else {
              <p class="text-sm text-warning-600 font-medium">
                No documents found with matching folder tags.
              </p>
              }
            </div>
          </div>
        </div>

        <!-- Suggestions List -->
        @if (suggestions().length > 0) {
        <div class="space-y-3">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-medium text-foreground">
              Organization Suggestions
            </h3>
            <button
              (click)="toggleSelectAll()"
              class="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-primary-600 border border-border hover:border-primary-500/50 rounded-md transition-colors"
            >
              <div class="relative">
                <input
                  type="checkbox"
                  [checked]="allSelected()"
                  [indeterminate]="someSelected()"
                  class="h-4 w-4 rounded border-border text-primary-600 focus:ring-primary-500"
                  (click)="toggleSelectAll(); $event.stopPropagation()"
                />
              </div>
              {{ allSelected() ? 'Deselect All' : 'Select All' }}
            </button>
          </div>
          @for (suggestion of displayedSuggestions(); track
          suggestion.document_id) {
          <div
            class="group p-4 bg-background border rounded-lg transition-all cursor-pointer"
            [class.border-primary-500]="isSelected(suggestion.document_id)"
            [class.border-border]="!isSelected(suggestion.document_id)"
            [ngClass]="{
                  'hover:border-primary-500/50': !isSelected(suggestion.document_id),
                }"
            [class.hover:shadow-sm]="!isSelected(suggestion.document_id)"
            (click)="toggleSelection(suggestion.document_id)"
            (keydown.space)="
              toggleSelection(suggestion.document_id); $event.preventDefault()
            "
            (keydown.enter)="
              toggleSelection(suggestion.document_id); $event.preventDefault()
            "
            tabindex="0"
            role="button"
            [attr.aria-pressed]="isSelected(suggestion.document_id)"
          >
            <div class="flex items-start gap-3">
              <!-- Checkbox -->
              <div class="pt-1">
                <input
                  type="checkbox"
                  [checked]="isSelected(suggestion.document_id)"
                  class="h-4 w-4 rounded border-border text-primary-600 focus:ring-primary-500"
                  (click)="
                    toggleSelection(suggestion.document_id);
                    $event.stopPropagation()
                  "
                />
              </div>

              <!-- Content -->
              <div class="flex-1 flex items-start justify-between gap-4">
                <!-- Document Info -->
                <div class="flex-1 min-w-0">
                  <h4 class="font-medium text-sm text-foreground truncate mb-2">
                    {{ suggestion.document_name }}
                  </h4>
                  <div class="flex flex-wrap gap-1.5">
                    @for (tag of suggestion.document_tags; track tag) { @if
                    (suggestion.matching_tags.includes(tag)) {
                    <span
                      class="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full transition-colors bg-primary-500/10 text-primary-700 ring-1 ring-primary-500/20"
                    >
                      <svg
                        class="w-3 h-3 mr-1"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fill-rule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clip-rule="evenodd"
                        />
                      </svg>
                      {{ tag }}
                    </span>
                    } @else {
                    <span
                      class="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full transition-colors bg-muted/50 text-muted-foreground"
                    >
                      {{ tag }}
                    </span>
                    } }
                  </div>
                </div>

                <!-- Arrow and Folder Info -->
                <div class="flex items-center gap-3">
                  <svg
                    class="w-5 h-5 text-muted-foreground/50 flex-shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M13 7l5 5m0 0l-5 5m5-5H6"
                    />
                  </svg>
                  <div class="text-right">
                    <div class="flex items-center gap-2 mb-1">
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
                          d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                        />
                      </svg>
                      <span class="text-sm font-medium text-foreground">{{
                        suggestion.suggested_folder_name
                      }}</span>
                    </div>
                    <div class="flex items-center gap-1 text-xs">
                      <div
                        class="px-2 py-0.5 rounded-full font-medium"
                        [class.bg-success-100]="
                          suggestion.similarity_score >= 0.7
                        "
                        [class.text-success-700]="
                          suggestion.similarity_score >= 0.7
                        "
                        [class.bg-warning-100]="
                          suggestion.similarity_score >= 0.4 &&
                          suggestion.similarity_score < 0.7
                        "
                        [class.text-warning-700]="
                          suggestion.similarity_score >= 0.4 &&
                          suggestion.similarity_score < 0.7
                        "
                        [class.bg-muted]="suggestion.similarity_score < 0.4"
                        [class.text-muted-foreground]="
                          suggestion.similarity_score < 0.4
                        "
                      >
                        {{ (suggestion.similarity_score * 100).toFixed(0) }}%
                        match
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          } @if (hasMore()) {
          <div class="mt-4 text-center">
            <button
              (click)="showAll.set(!showAll())"
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-primary-600 hover:text-primary-700 hover:bg-primary-50 rounded-lg transition-colors"
            >
              @if (showAll()) {
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
                  d="M5 15l7-7 7 7"
                />
              </svg>
              Show less } @else {
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
                  d="M19 9l-7 7-7-7"
                />
              </svg>
              Show all {{ suggestions().length }} suggestions }
            </button>
          </div>
          }
        </div>
        }
      </div>

      <!-- Footer -->
      <div class="modal-footer p-6 border-t border-border bg-muted/5">
        <div class="flex items-center gap-3 justify-between">
          <div class="text-sm text-muted-foreground">
            @if (selectedCount() > 0) {
            {{ selectedCount() }} of {{ suggestions().length }} selected
            } @else if (suggestions().length > 0) {
            No documents selected
            }
          </div>
          <div class="flex items-center gap-3">
            <button
              (click)="cancel()"
              class="px-4 py-2.5 text-sm font-medium text-foreground bg-background border border-border rounded-lg hover:bg-muted/50 transition-all"
            >
              Cancel
            </button>
            <button
              (click)="organize()"
              [disabled]="selectedCount() === 0"
              class="px-6 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-primary-600 to-accent-600 rounded-lg hover:shadow-lg transform hover:scale-[1.02] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
            >
              <span class="flex items-center gap-2">
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
                    d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                  />
                </svg>
                Organize {{ selectedCount() }}
                {{ selectedCount() === 1 ? 'Document' : 'Documents' }}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class OrganizeDialog implements OnInit {
  private modalRef = inject<ModalRef<OrganizeDialogResult>>(MODAL_REF);

  // Input properties using new Angular syntax
  suggestions = input<OrganizeSuggestion[]>([]);
  totalUnfiled = input(0);
  totalWithTags = input(0);

  protected showAll = signal(false);
  protected readonly MAX_INITIAL_DISPLAY = 10;

  // Selection state
  protected selectedIds = signal<Set<string>>(new Set());

  protected displayedSuggestions = computed(() => {
    const suggestionsList = this.suggestions();
    if (this.showAll() || suggestionsList.length <= this.MAX_INITIAL_DISPLAY) {
      return suggestionsList;
    }
    return suggestionsList.slice(0, this.MAX_INITIAL_DISPLAY);
  });

  protected hasMore = computed(
    () => this.suggestions().length > this.MAX_INITIAL_DISPLAY
  );

  protected selectedCount = computed(() => this.selectedIds().size);

  protected allSelected = computed(
    () =>
      this.suggestions().length > 0 &&
      this.selectedIds().size === this.suggestions().length
  );

  protected someSelected = computed(
    () =>
      this.selectedIds().size > 0 &&
      this.selectedIds().size < this.suggestions().length
  );

  ngOnInit() {
    // Select all suggestions by default
    const allIds = new Set(this.suggestions().map((s) => s.document_id));
    this.selectedIds.set(allIds);
  }

  toggleSelection(documentId: string) {
    this.selectedIds.update((ids) => {
      const newIds = new Set(ids);
      if (newIds.has(documentId)) {
        newIds.delete(documentId);
      } else {
        newIds.add(documentId);
      }
      return newIds;
    });
  }

  toggleSelectAll() {
    if (this.allSelected()) {
      this.selectedIds.set(new Set());
    } else {
      const allIds = new Set(this.suggestions().map((s) => s.document_id));
      this.selectedIds.set(allIds);
    }
  }

  isSelected(documentId: string): boolean {
    return this.selectedIds().has(documentId);
  }

  cancel() {
    this.modalRef.dismiss();
  }

  organize() {
    const selectedAssignments = this.suggestions()
      .filter((s) => this.selectedIds().has(s.document_id))
      .map((s) => ({
        documentId: s.document_id,
        folderId: s.suggested_folder_id,
      }));

    this.modalRef.dismiss({
      organize: true,
      selectedAssignments,
    });
  }
}
