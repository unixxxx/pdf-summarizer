import {
  Component,
  OnInit,
  inject,
  ChangeDetectionStrategy,
  signal,
  computed,
} from '@angular/core';

import {
  trigger,
  style,
  transition,
  animate,
  state,
} from '@angular/animations';
import { ArchiveStore } from '../archive.store';
import { ArchivedDocument, ArchivedFolderWithChildren } from '../archive.model';
import { ArchiveRestoreDialogComponent } from '../components/archive-restore-dialog.component';
import { ArchiveEmptyDialogComponent } from '../components/archive-empty-dialog.component';
import { ArchiveDeleteDialogComponent } from '../components/archive-delete-dialog.component';
import { formatFileSize } from '../../../core/utils/file-size.formatter';
import { formatDate } from '../../../core/utils/date.formatter';

@Component({
  selector: 'app-archive',
  standalone: true,
  imports: [
    ArchiveRestoreDialogComponent,
    ArchiveEmptyDialogComponent,
    ArchiveDeleteDialogComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [
    trigger('fadeIn', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('300ms ease-out', style({ opacity: 1 })),
      ]),
    ]),
    trigger('listItem', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(-10px)' }),
        animate(
          '200ms ease-out',
          style({ opacity: 1, transform: 'translateY(0)' })
        ),
      ]),
    ]),
    trigger('expandCollapse', [
      state(
        'collapsed',
        style({ height: '0', opacity: 0, overflow: 'hidden' })
      ),
      state('expanded', style({ height: '*', opacity: 1 })),
      transition('collapsed <=> expanded', animate('200ms ease-in-out')),
    ]),
  ],
  template: `
    <div class="h-screen flex flex-col">
      <!-- Stats Bar -->
      @if (archiveStore.stats()) {
      <div
        class="flex-shrink-0 px-4 sm:px-6 py-3 glass border-b border-border/50"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4 text-sm text-muted-foreground">
            <span>{{ archiveStore.stats()!.total_documents }} documents</span>
            <span>•</span>
            <span>{{ archiveStore.stats()!.total_folders }} folders</span>
            <span>•</span>
            <span>{{ formatFileSize(archiveStore.stats()!.total_size) }}</span>
          </div>
          @if (archiveStore.canEmpty()) {
          <button
            (click)="emptyArchive()"
            class="px-3 py-1.5 text-sm font-medium text-white bg-error hover:bg-error/90 rounded-lg transition-colors"
          >
            Empty Archive
          </button>
          }
        </div>
      </div>
      }

      <!-- Content -->
      <div class="flex-1 overflow-y-auto p-4 sm:p-6">
        @if (archiveStore.loading()) {
        <div class="flex items-center justify-center h-64">
          <div
            class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"
          ></div>
        </div>
        } @else if (archiveStore.isEmpty()) {
        <div
          class="flex flex-col items-center justify-center h-64 text-muted-foreground"
        >
          <svg
            class="w-16 h-16 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
          <p class="text-lg">Archive is empty</p>
          <p class="text-sm mt-2">Items you archive will appear here</p>
        </div>
        } @else {
        <div class="space-y-2">
          <!-- Tree View for Folders and Root Documents -->
          @for (folder of archiveStore.archivedFolders(); track folder.id) {
          <div @listItem>
            <!-- Folder Item -->
            <div
              class="glass rounded-xl hover:shadow-lg transition-all group overflow-hidden"
            >
              <div class="p-4">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-3 flex-1">
                    <button
                      (click)="toggleFolder(folder.id)"
                      class="p-1 hover:bg-muted rounded transition-colors"
                      [class.rotate-90]="expandedFolders().has(folder.id)"
                      [disabled]="!hasContents(folder)"
                    >
                      <svg
                        class="w-4 h-4 transition-transform"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M9 5l7 7-7 7"
                        />
                      </svg>
                    </button>
                    <svg
                      class="w-5 h-5 text-muted-foreground flex-shrink-0"
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
                    <div class="flex-1 min-w-0">
                      <p class="font-medium text-foreground truncate">
                        {{ folder.name }}
                      </p>
                      <p class="text-sm text-muted-foreground">
                        Archived {{ formatDate(folder.archived_at) }}
                        @if (folder.document_count > 0 || folder.children_count
                        > 0) { • Contains: @if (folder.document_count > 0) {
                        {{ folder.document_count }}
                        {{
                          folder.document_count === 1 ? 'document' : 'documents'
                        }}
                        } @if (folder.document_count > 0 &&
                        folder.children_count > 0) { , } @if
                        (folder.children_count > 0) {
                        {{ folder.children_count }}
                        {{
                          folder.children_count === 1
                            ? 'subfolder'
                            : 'subfolders'
                        }}
                        } } @if (folder.parent_name) { • Was in
                        {{ folder.parent_name }}
                        }
                      </p>
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <button
                      (click)="restoreFolder(folder)"
                      class="opacity-0 group-hover:opacity-100 px-3 py-1.5 text-sm text-primary hover:bg-primary/10 rounded-lg transition-all"
                    >
                      Restore
                    </button>
                    <button
                      (click)="deleteFolder(folder)"
                      class="opacity-0 group-hover:opacity-100 px-3 py-1.5 text-sm text-error hover:bg-error/10 rounded-lg transition-all"
                      title="Delete permanently"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>

              <!-- Folder Contents -->
              @if (hasContents(folder)) {
              <div
                [@expandCollapse]="
                  expandedFolders().has(folder.id) ? 'expanded' : 'collapsed'
                "
                class="border-t border-border/50"
              >
                <div class="pl-12 pr-4 py-2 space-y-1">
                  <!-- Child Folders -->
                  @for (childFolder of folder.children; track childFolder.id) {
                  <div
                    class="border border-border/30 rounded-lg overflow-hidden"
                  >
                    <div
                      class="py-2 hover:bg-muted/30 transition-colors group/child"
                    >
                      <div class="flex items-center justify-between px-3">
                        <div class="flex items-center gap-3 flex-1 min-w-0">
                          <button
                            (click)="toggleFolder(childFolder.id)"
                            class="p-0.5 hover:bg-muted rounded transition-colors"
                            [class.rotate-90]="
                              expandedFolders().has(childFolder.id)
                            "
                            [disabled]="!hasContents(childFolder)"
                          >
                            <svg
                              class="w-3 h-3 transition-transform"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M9 5l7 7-7 7"
                              />
                            </svg>
                          </button>
                          <svg
                            class="w-4 h-4 text-muted-foreground flex-shrink-0"
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
                          <div class="flex-1 min-w-0">
                            <p
                              class="text-sm font-medium text-foreground truncate"
                            >
                              {{ childFolder.name }}
                            </p>
                            <p class="text-xs text-muted-foreground">
                              @if (childFolder.document_count > 0 ||
                              childFolder.children_count > 0) { Contains: @if
                              (childFolder.document_count > 0) {
                              {{ childFolder.document_count }}
                              {{
                                childFolder.document_count === 1
                                  ? 'document'
                                  : 'documents'
                              }}
                              } @if (childFolder.document_count > 0 &&
                              childFolder.children_count > 0) { , } @if
                              (childFolder.children_count > 0) {
                              {{ childFolder.children_count }}
                              {{
                                childFolder.children_count === 1
                                  ? 'subfolder'
                                  : 'subfolders'
                              }}
                              } }
                            </p>
                          </div>
                        </div>
                        <div class="flex items-center gap-1">
                          <button
                            (click)="
                              restoreFolder(childFolder);
                              $event.stopPropagation()
                            "
                            class="opacity-0 group-hover/child:opacity-100 px-2 py-1 text-xs text-primary hover:bg-primary/10 rounded transition-all"
                          >
                            Restore
                          </button>
                          <button
                            (click)="
                              deleteFolder(childFolder);
                              $event.stopPropagation()
                            "
                            class="opacity-0 group-hover/child:opacity-100 px-2 py-1 text-xs text-error hover:bg-error/10 rounded transition-all"
                            title="Delete permanently"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    </div>

                    <!-- Nested folder contents -->
                    @if (hasContents(childFolder)) {
                    <div
                      [@expandCollapse]="
                        expandedFolders().has(childFolder.id)
                          ? 'expanded'
                          : 'collapsed'
                      "
                      class="border-t border-border/30"
                    >
                      <div class="pl-8 pr-3 py-1 space-y-1">
                        <!-- Documents in nested folder -->
                        @for (doc of childFolder.documents; track doc.id) {
                        <div
                          class="py-1.5 hover:bg-muted/30 rounded transition-colors group/doc"
                        >
                          <div class="flex items-center justify-between px-2">
                            <div class="flex items-center gap-2 flex-1 min-w-0">
                              <svg
                                class="w-3 h-3 text-muted-foreground flex-shrink-0"
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
                              <div class="flex-1 min-w-0">
                                <p
                                  class="text-xs font-medium text-foreground truncate"
                                >
                                  {{ doc.name }}
                                </p>
                                <p class="text-xs text-muted-foreground">
                                  {{ formatFileSize(doc.file_size) }}
                                  @if (doc.page_count) { • {{ doc.page_count }}
                                  {{ doc.page_count === 1 ? 'page' : 'pages' }}
                                  }
                                </p>
                              </div>
                            </div>
                            <div class="flex items-center gap-1">
                              <button
                                (click)="
                                  restoreDocument(doc); $event.stopPropagation()
                                "
                                class="opacity-0 group-hover/doc:opacity-100 px-1.5 py-0.5 text-xs text-primary hover:bg-primary/10 rounded transition-all"
                              >
                                Restore
                              </button>
                              <button
                                (click)="
                                  deleteDocument(doc); $event.stopPropagation()
                                "
                                class="opacity-0 group-hover/doc:opacity-100 px-1.5 py-0.5 text-xs text-error hover:bg-error/10 rounded transition-all"
                                title="Delete permanently"
                              >
                                Delete
                              </button>
                            </div>
                          </div>
                        </div>
                        }
                      </div>
                    </div>
                    }
                  </div>
                  }

                  <!-- Documents in Folder -->
                  @for (doc of folder.documents; track doc.id) {
                  <div
                    class="py-2 hover:bg-muted/30 rounded-lg transition-colors group/child"
                  >
                    <div class="flex items-center justify-between px-3">
                      <div class="flex items-center gap-3 flex-1 min-w-0">
                        <svg
                          class="w-4 h-4 text-muted-foreground flex-shrink-0"
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
                        <div class="flex-1 min-w-0">
                          <p
                            class="text-sm font-medium text-foreground truncate"
                          >
                            {{ doc.name }}
                          </p>
                          <p class="text-xs text-muted-foreground">
                            {{ formatFileSize(doc.file_size) }}
                            @if (doc.page_count) { • {{ doc.page_count }}
                            {{ doc.page_count === 1 ? 'page' : 'pages' }}
                            }
                          </p>
                        </div>
                      </div>
                      <div class="flex items-center gap-1">
                        <button
                          (click)="
                            restoreDocument(doc); $event.stopPropagation()
                          "
                          class="opacity-0 group-hover/child:opacity-100 px-2 py-1 text-xs text-primary hover:bg-primary/10 rounded transition-all"
                        >
                          Restore
                        </button>
                        <button
                          (click)="
                            deleteDocument(doc); $event.stopPropagation()
                          "
                          class="opacity-0 group-hover/child:opacity-100 px-2 py-1 text-xs text-error hover:bg-error/10 rounded transition-all"
                          title="Delete permanently"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                  }
                </div>
              </div>
              }
            </div>
          </div>
          }

          <!-- Root Documents (not in any folder) -->
          @for (doc of rootDocuments(); track doc.id) {
          <div
            @listItem
            class="glass rounded-xl p-4 hover:shadow-lg transition-all group"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-5"></div>
                <!-- Spacer to align with folders -->
                <svg
                  class="w-5 h-5 text-muted-foreground"
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
                <div>
                  <p class="font-medium text-foreground">{{ doc.name }}</p>
                  <p class="text-sm text-muted-foreground">
                    {{ formatFileSize(doc.file_size) }} • Archived
                    {{ formatDate(doc.archived_at) }} @if (doc.page_count) { •
                    {{ doc.page_count }}
                    {{ doc.page_count === 1 ? 'page' : 'pages' }}
                    }
                  </p>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <button
                  (click)="restoreDocument(doc)"
                  class="opacity-0 group-hover:opacity-100 px-3 py-1.5 text-sm text-primary hover:bg-primary/10 rounded-lg transition-all"
                >
                  Restore
                </button>
                <button
                  (click)="deleteDocument(doc)"
                  class="opacity-0 group-hover:opacity-100 px-3 py-1.5 text-sm text-error hover:bg-error/10 rounded-lg transition-all"
                  title="Delete permanently"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
          }
        </div>
        }
      </div>
    </div>

    <!-- Restore Confirmation Dialog -->
    <app-archive-restore-dialog
      [show]="showRestoreDialog()"
      [itemName]="restoreItem()?.name || ''"
      [isFolder]="restoreItemIsFolder()"
      [parentName]="restoreItemParentName()"
      [documentCount]="restoreItemDocumentCount()"
      [childrenCount]="restoreItemChildrenCount()"
      (confirm)="confirmRestore()"
      (canceled)="cancelRestore()"
    />

    <!-- Empty Archive Confirmation Dialog -->
    <app-archive-empty-dialog
      [show]="showEmptyDialog()"
      [documentCount]="archiveStore.stats()?.total_documents || 0"
      [folderCount]="archiveStore.stats()?.total_folders || 0"
      [totalSize]="archiveStore.stats()?.total_size || 0"
      (confirm)="confirmEmptyArchive()"
      (canceled)="cancelEmptyArchive()"
    />

    <!-- Delete Item Confirmation Dialog -->
    <app-archive-delete-dialog
      [show]="showDeleteDialog()"
      [itemName]="deleteItem()?.name || ''"
      [isFolder]="deleteItemIsFolder()"
      [documentCount]="deleteItemDocumentCount()"
      [childrenCount]="deleteItemChildrenCount()"
      (confirm)="confirmDelete()"
      (canceled)="cancelDelete()"
    />
  `,
})
export class ArchiveComponent implements OnInit {
  protected archiveStore = inject(ArchiveStore);

  formatFileSize = formatFileSize;
  formatDate = formatDate;

  // Restore dialog state
  showRestoreDialog = signal(false);
  restoreItem = signal<ArchivedDocument | ArchivedFolderWithChildren | null>(
    null
  );
  restoreItemType = signal<'document' | 'folder'>('document');

  // Empty archive dialog state
  showEmptyDialog = signal(false);

  // Delete dialog state
  showDeleteDialog = signal(false);
  deleteItem = signal<ArchivedDocument | ArchivedFolderWithChildren | null>(
    null
  );
  deleteItemType = signal<'document' | 'folder'>('document');

  // Tree view state
  expandedFolders = signal(new Set<string>());

  // Computed property for root documents
  rootDocuments = computed(() => {
    const allDocs = this.archiveStore.archivedDocuments();
    const folderDocs = new Set<string>();

    // Collect all document IDs that are in folders
    this.archiveStore.archivedFolders().forEach((folder) => {
      folder.documents?.forEach((doc) => folderDocs.add(doc.id));
    });

    // Return only documents not in any folder
    return allDocs.filter((doc) => !folderDocs.has(doc.id));
  });

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

  // Computed properties for delete dialog
  deleteItemIsFolder = () => this.deleteItemType() === 'folder';
  deleteItemDocumentCount = () => {
    const item = this.deleteItem();
    return item && 'document_count' in item ? item.document_count : 0;
  };
  deleteItemChildrenCount = () => {
    const item = this.deleteItem();
    return item && 'children_count' in item ? item.children_count : 0;
  };

  ngOnInit() {
    this.archiveStore.loadArchiveContent();
  }

  restoreFolder(folder: ArchivedFolderWithChildren) {
    this.restoreItem.set(folder);
    this.restoreItemType.set('folder');
    this.showRestoreDialog.set(true);
  }

  restoreDocument(doc: ArchivedDocument) {
    this.restoreItem.set(doc);
    this.restoreItemType.set('document');
    this.showRestoreDialog.set(true);
  }

  confirmRestore() {
    const item = this.restoreItem();
    if (!item) return;

    if (this.restoreItemType() === 'folder') {
      this.archiveStore.restoreFolder(item as ArchivedFolderWithChildren);
    } else {
      this.archiveStore.restoreDocument(item as ArchivedDocument);
    }

    this.cancelRestore();
  }

  cancelRestore() {
    this.showRestoreDialog.set(false);
    this.restoreItem.set(null);
  }

  emptyArchive() {
    this.showEmptyDialog.set(true);
  }

  confirmEmptyArchive() {
    this.archiveStore.emptyArchive();
    this.cancelEmptyArchive();
  }

  cancelEmptyArchive() {
    this.showEmptyDialog.set(false);
  }

  toggleFolder(folderId: string) {
    const expanded = new Set(this.expandedFolders());
    if (expanded.has(folderId)) {
      expanded.delete(folderId);
    } else {
      expanded.add(folderId);
    }
    this.expandedFolders.set(expanded);
  }

  hasContents(folder: ArchivedFolderWithChildren): boolean {
    return folder.children?.length > 0 || folder.documents?.length > 0;
  }

  deleteFolder(folder: ArchivedFolderWithChildren) {
    this.deleteItem.set(folder);
    this.deleteItemType.set('folder');
    this.showDeleteDialog.set(true);
  }

  deleteDocument(doc: ArchivedDocument) {
    this.deleteItem.set(doc);
    this.deleteItemType.set('document');
    this.showDeleteDialog.set(true);
  }

  confirmDelete() {
    const item = this.deleteItem();
    if (!item) return;

    if (this.deleteItemType() === 'folder') {
      this.archiveStore.deleteFolder(item as ArchivedFolderWithChildren);
    } else {
      this.archiveStore.deleteDocument(item as ArchivedDocument);
    }

    this.cancelDelete();
  }

  cancelDelete() {
    this.showDeleteDialog.set(false);
    this.deleteItem.set(null);
  }
}
