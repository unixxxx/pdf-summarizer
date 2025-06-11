import { Component, OnInit, inject, ChangeDetectionStrategy, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { trigger, style, transition, animate } from '@angular/animations';
import { TrashStore } from '../trash.store';
import { TrashedDocument, TrashedFolderWithChildren } from '../trash.model';
import { TrashRestoreDialogComponent } from '../components/trash-restore-dialog.component';
import { TrashEmptyDialogComponent } from '../components/trash-empty-dialog.component';
import { formatFileSize } from '../../../shared/utils/formatters/file-size.formatter';
import { formatDate } from '../../../shared/utils/formatters/date.formatter';

@Component({
  selector: 'app-trash',
  standalone: true,
  imports: [CommonModule, RouterLink, TrashRestoreDialogComponent, TrashEmptyDialogComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [
    trigger('fadeIn', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('300ms ease-out', style({ opacity: 1 }))
      ])
    ]),
    trigger('listItem', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(-10px)' }),
        animate('200ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ])
  ],
  template: `
    <div class="h-screen flex flex-col bg-background">
      <!-- Header -->
      <div class="flex-shrink-0 border-b border-border px-4 sm:px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <button
              routerLink="/app/library"
              class="p-2 hover:bg-muted rounded-lg transition-colors"
              title="Back to Library"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <div>
              <h2 class="text-xl sm:text-2xl font-bold text-foreground">Trash</h2>
              <p class="mt-1 text-xs sm:text-sm text-muted-foreground hidden sm:block">
                Items you have deleted
              </p>
            </div>
          </div>
          
          @if (trashStore.canEmpty()) {
            <button
              (click)="emptyTrash()"
              class="px-4 py-2 text-sm font-medium text-white bg-error hover:bg-error/90 rounded-lg transition-colors"
            >
              Empty Trash
            </button>
          }
        </div>
      </div>

      <!-- Stats Bar -->
      @if (trashStore.stats()) {
        <div class="flex-shrink-0 px-4 sm:px-6 py-3 bg-muted/30 border-b border-border">
          <div class="flex items-center gap-4 text-sm text-muted-foreground">
            <span>{{ trashStore.stats()!.total_documents }} documents</span>
            <span>•</span>
            <span>{{ trashStore.stats()!.total_folders }} folders</span>
            <span>•</span>
            <span>{{ formatFileSize(trashStore.stats()!.total_size) }}</span>
          </div>
        </div>
      }

      <!-- Content -->
      <div class="flex-1 overflow-y-auto p-4 sm:p-6">
        @if (trashStore.loading()) {
          <div class="flex items-center justify-center h-64">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        } @else if (trashStore.isEmpty()) {
          <div class="flex flex-col items-center justify-center h-64 text-muted-foreground">
            <svg class="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            <p class="text-lg">Trash is empty</p>
            <p class="text-sm mt-2">Items you delete will appear here</p>
          </div>
        } @else {
          <!-- Folders Section -->
          @if (trashStore.trashedFolders().length > 0) {
            <div class="mb-8">
              <h3 class="text-lg font-medium text-foreground mb-4">Folders</h3>
              <div class="space-y-2">
                @for (folder of trashStore.trashedFolders(); track folder.id) {
                  <div 
                    @listItem
                    class="glass rounded-xl p-4 hover:shadow-lg transition-all group"
                  >
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-3">
                        <svg class="w-5 h-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                        </svg>
                        <div>
                          <p class="font-medium text-foreground">{{ folder.name }}</p>
                          <p class="text-sm text-muted-foreground">
                            Deleted {{ formatDate(folder.deleted_at) }}
                            @if (folder.document_count > 0) {
                              • {{ folder.document_count }} documents
                            }
                            @if (folder.children_count > 0) {
                              • {{ folder.children_count }} subfolders
                            }
                            @if (folder.parent_name) {
                              • Was in {{ folder.parent_name }}
                            }
                          </p>
                        </div>
                      </div>
                      <button
                        (click)="restoreFolder(folder)"
                        class="opacity-0 group-hover:opacity-100 px-3 py-1.5 text-sm text-primary hover:bg-primary/10 rounded-lg transition-all"
                      >
                        Restore
                      </button>
                    </div>
                  </div>
                }
              </div>
            </div>
          }

          <!-- Documents Section -->
          @if (trashStore.trashedDocuments().length > 0) {
            <div>
              <h3 class="text-lg font-medium text-foreground mb-4">Documents</h3>
              <div class="space-y-2">
                @for (doc of trashStore.trashedDocuments(); track doc.id) {
                  <div 
                    @listItem
                    class="glass rounded-xl p-4 hover:shadow-lg transition-all group"
                  >
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-3">
                        <svg class="w-5 h-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <div>
                          <p class="font-medium text-foreground">{{ doc.name }}</p>
                          <p class="text-sm text-muted-foreground">
                            {{ formatFileSize(doc.file_size) }} • Deleted {{ formatDate(doc.deleted_at) }}
                            @if (doc.folder_name) {
                              • Was in {{ doc.folder_name }}
                            }
                          </p>
                        </div>
                      </div>
                      <button
                        (click)="restoreDocument(doc)"
                        class="opacity-0 group-hover:opacity-100 px-3 py-1.5 text-sm text-primary hover:bg-primary/10 rounded-lg transition-all"
                      >
                        Restore
                      </button>
                    </div>
                  </div>
                }
              </div>
            </div>
          }
        }
      </div>
    </div>

    <!-- Restore Confirmation Dialog -->
    <app-trash-restore-dialog
      [show]="showRestoreDialog()"
      [itemName]="restoreItem()?.name || ''"
      [isFolder]="restoreItemIsFolder()"
      [parentName]="restoreItemParentName()"
      [documentCount]="restoreItemDocumentCount()"
      [childrenCount]="restoreItemChildrenCount()"
      (confirm)="confirmRestore()"
      (canceled)="cancelRestore()"
    />

    <!-- Empty Trash Confirmation Dialog -->
    <app-trash-empty-dialog
      [show]="showEmptyDialog()"
      [documentCount]="trashStore.stats()?.total_documents || 0"
      [folderCount]="trashStore.stats()?.total_folders || 0"
      [totalSize]="trashStore.stats()?.total_size || 0"
      (confirm)="confirmEmptyTrash()"
      (canceled)="cancelEmptyTrash()"
    />
  `,
})
export class TrashComponent implements OnInit {
  protected trashStore = inject(TrashStore);

  formatFileSize = formatFileSize;
  formatDate = formatDate;

  // Restore dialog state
  showRestoreDialog = signal(false);
  restoreItem = signal<TrashedDocument | TrashedFolderWithChildren | null>(null);
  restoreItemType = signal<'document' | 'folder'>('document');
  
  // Empty trash dialog state
  showEmptyDialog = signal(false);

  // Computed properties for dialog
  restoreItemIsFolder = () => this.restoreItemType() === 'folder';
  restoreItemParentName = () => {
    const item = this.restoreItem();
    if (!item) return null;
    if ('parent_name' in item) {
      return item.parent_name;
    } else if ('folder_name' in item) {
      return item.folder_name;
    }
    return null;
  };
  restoreItemDocumentCount = () => {
    const item = this.restoreItem();
    return item && 'document_count' in item ? item.document_count : 0;
  };
  restoreItemChildrenCount = () => {
    const item = this.restoreItem();
    return item && 'children_count' in item ? item.children_count : 0;
  };

  ngOnInit() {
    this.trashStore.loadTrashContent();
  }

  restoreFolder(folder: TrashedFolderWithChildren) {
    this.restoreItem.set(folder);
    this.restoreItemType.set('folder');
    this.showRestoreDialog.set(true);
  }

  restoreDocument(doc: TrashedDocument) {
    this.restoreItem.set(doc);
    this.restoreItemType.set('document');
    this.showRestoreDialog.set(true);
  }

  confirmRestore() {
    const item = this.restoreItem();
    if (!item) return;

    if (this.restoreItemType() === 'folder') {
      this.trashStore.restoreFolder(item as TrashedFolderWithChildren);
    } else {
      this.trashStore.restoreDocument(item as TrashedDocument);
    }
    
    this.cancelRestore();
  }

  cancelRestore() {
    this.showRestoreDialog.set(false);
    this.restoreItem.set(null);
  }

  emptyTrash() {
    this.showEmptyDialog.set(true);
  }

  confirmEmptyTrash() {
    this.trashStore.emptyTrash();
    this.cancelEmptyTrash();
  }

  cancelEmptyTrash() {
    this.showEmptyDialog.set(false);
  }
}