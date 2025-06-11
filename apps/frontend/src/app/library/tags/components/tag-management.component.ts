import { Component, inject, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LibraryStore } from '../../library.store';
import { TagComponent } from './tag.component';
import { Tag } from '../tag.model';

@Component({
  selector: 'app-tag-management',
  standalone: true,
  imports: [CommonModule, FormsModule, TagComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="p-4">
      <h3 class="text-lg font-semibold mb-4">Manage Tags</h3>
      
      @if (libraryStore.tagsLoading()) {
        <div class="text-center py-4">
          <span class="text-muted-foreground">Loading tags...</span>
        </div>
      } @else if (libraryStore.tagsIsEmpty()) {
        <div class="text-center py-8">
          <p class="text-muted-foreground">No tags yet. Tags will be automatically generated when you upload documents.</p>
        </div>
      } @else {
        <div class="space-y-3">
          @for (tag of libraryStore.popularTags(); track tag.id) {
            <div class="flex items-center justify-between p-3 bg-card border border-border rounded-lg">
              <div class="flex items-center gap-3">
                <app-tag [tag]="tag" variant="default" />
                <span class="text-sm text-muted-foreground">
                  {{ tag.documentCount || 0 }} {{ tag.documentCount === 1 ? 'document' : 'documents' }}
                </span>
              </div>
              
              <div class="flex items-center gap-2">
                @if (!editingTag || editingTag.id !== tag.id) {
                  <button
                    (click)="startEdit(tag)"
                    class="p-1 hover:bg-muted rounded"
                    title="Edit tag"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                        d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    (click)="deleteTag(tag)"
                    class="p-1 hover:bg-error/20 hover:text-error rounded"
                    title="Delete tag"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                } @else {
                  <!-- Edit form -->
                  <input
                    [(ngModel)]="editForm.name"
                    (keydown.enter)="saveEdit()"
                    (keydown.escape)="cancelEdit()"
                    class="px-2 py-1 text-sm border border-border rounded"
                    placeholder="Tag name"
                  />
                  <input
                    [(ngModel)]="editForm.color"
                    type="color"
                    (change)="saveEdit()"
                    class="w-8 h-8 border border-border rounded cursor-pointer"
                    title="Tag color"
                  />
                  <button
                    (click)="saveEdit()"
                    class="p-1 hover:bg-success/20 hover:text-success rounded"
                    title="Save"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    </svg>
                  </button>
                  <button
                    (click)="cancelEdit()"
                    class="p-1 hover:bg-muted rounded"
                    title="Cancel"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                }
              </div>
            </div>
          }
        </div>
      }
    </div>
  `,
})
export class TagManagementComponent {
  protected libraryStore = inject(LibraryStore);
  
  editingTag: Tag | null = null;
  editForm = {
    name: '',
    color: '',
  };

  constructor() {
    this.libraryStore.loadTags();
  }

  startEdit(tag: Tag) {
    this.editingTag = tag;
    this.editForm = {
      name: tag.name,
      color: tag.color,
    };
  }

  saveEdit() {
    if (this.editingTag && this.editForm.name) {
      this.libraryStore.updateTag({
        tagId: this.editingTag.id,
        updates: {
          name: this.editForm.name,
          color: this.editForm.color,
        },
      });
      this.cancelEdit();
    }
  }

  cancelEdit() {
    this.editingTag = null;
    this.editForm = { name: '', color: '' };
  }

  deleteTag(tag: Tag) {
    if (confirm(`Are you sure you want to delete the tag "${tag.name}"?`)) {
      this.libraryStore.deleteTag(tag.id);
    }
  }
}