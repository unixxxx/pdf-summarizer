import {
  Component,
  inject,
  ChangeDetectionStrategy,
  signal,
  computed,
} from '@angular/core';
import { Store } from '@ngrx/store';
import {
  trigger,
  style,
  transition,
  animate,
  state,
} from '@angular/animations';
import { ArchiveActions } from '../store/archive.actions';
import { archiveFeature } from '../store/archive.feature';
import { ArchivedDocument } from '../store/state/archived-document';
import { ArchivedFolderWithChildren } from '../store/state/archived-folder-with-children';
import { FormatDatePipe } from '../../../core/pipes/formatDate';
import { FormatFileSizePipe } from '../../../core/pipes/formatFileSize';

@Component({
  selector: 'app-archive',
  standalone: true,
  imports: [FormatDatePipe, FormatFileSizePipe],
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
    @let statsData = stats(); @let foldersData = folders(); @let isEmptyData =
    isEmpty(); @let canEmptyData = canEmpty(); @let isLoadingData = isLoading();

    <div class="h-screen flex flex-col">
      <!-- Stats Bar -->
      @if (statsData) {
      <div
        class="flex-shrink-0 px-4 sm:px-6 py-3 glass border-b border-border/50"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4 text-sm text-muted-foreground">
            <span>{{ statsData.totalDocuments || 0 }} documents</span>
            <span>•</span>
            <span>{{ statsData.totalFolders || 0 }} folders</span>
            <span>•</span>
            <span>{{ statsData.totalSize || 0 | formatFileSize }}</span>
            @if (statsData.totalDocuments > 0 && (!rootDocuments() ||
            rootDocuments()!.length === 0) && foldersData.length > 0) {
            <span>•</span>
            <span class="text-xs">(documents are in folders)</span>
            }
          </div>
          @if (canEmptyData) {
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
        @if (isLoadingData) {
        <div class="flex items-center justify-center h-64">
          <div
            class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"
          ></div>
        </div>
        } @else if (isEmptyData) {
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
          @for (folder of foldersData || []; track folder.id) {
          <div @listItem>
            <!-- Folder Item -->
            <div
              class="glass rounded-xl hover:shadow-lg transition-all group overflow-hidden"
            >
              <div class="p-4">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-3 flex-1">
                    @if (hasContents(folder)) {
                    <button
                      (click)="toggleFolder(folder.id)"
                      class="p-1 hover:bg-muted rounded transition-colors"
                      [class.rotate-90]="expandedFolders().has(folder.id)"
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
                    } @else {
                    <div class="w-6 h-6"></div>
                    }
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
                        Archived {{ folder.archivedAt | formatDate }}
                        @if (folder.documentCount > 0 || folder.childrenCount >
                        0) { • Contains: @if (folder.documentCount > 0) {
                        {{ folder.documentCount }}
                        {{
                          folder.documentCount === 1 ? 'document' : 'documents'
                        }}
                        } @if (folder.documentCount > 0 && folder.childrenCount
                        > 0) { , } @if (folder.childrenCount > 0) {
                        {{ folder.childrenCount }}
                        {{
                          folder.childrenCount === 1
                            ? 'subfolder'
                            : 'subfolders'
                        }}
                        } } @if (folder.parentName) { • Was in
                        {{ folder.parentName }}
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
                          @if (hasContents(childFolder)) {
                          <button
                            (click)="toggleFolder(childFolder.id)"
                            class="p-0.5 hover:bg-muted rounded transition-colors"
                            [class.rotate-90]="
                              expandedFolders().has(childFolder.id)
                            "
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
                          } @else {
                          <div class="w-4 h-4"></div>
                          }
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
                              @if (childFolder.documentCount > 0 ||
                              childFolder.childrenCount > 0) { Contains: @if
                              (childFolder.documentCount > 0) {
                              {{ childFolder.documentCount }}
                              {{
                                childFolder.documentCount === 1
                                  ? 'document'
                                  : 'documents'
                              }}
                              } @if (childFolder.documentCount > 0 &&
                              childFolder.childrenCount > 0) { , } @if
                              (childFolder.childrenCount > 0) {
                              {{ childFolder.childrenCount }}
                              {{
                                childFolder.childrenCount === 1
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
                                  {{ doc.fileSize | formatFileSize }}
                                  @if (doc.pageCount) { • {{ doc.pageCount }}
                                  {{ doc.pageCount === 1 ? 'page' : 'pages' }}
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
                            {{ doc.fileSize | formatFileSize }}
                            @if (doc.pageCount) { • {{ doc.pageCount }}
                            {{ doc.pageCount === 1 ? 'page' : 'pages' }}
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
          <!-- Note: Documents inside archived folders are shown nested within their folders above -->
          @for (doc of rootDocuments() || []; track doc.id) {
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
                    {{ doc.fileSize | formatFileSize }} • Archived
                    {{ doc.archivedAt | formatDate }} @if (doc.pageCount) { •
                    {{ doc.pageCount }}
                    {{ doc.pageCount === 1 ? 'page' : 'pages' }}
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
  `,
})
export class Archive {
  protected readonly store = inject(Store);

  // Store signals
  protected readonly archive = this.store.selectSignal(
    archiveFeature.selectArchive
  );
  protected readonly stats = this.store.selectSignal(
    archiveFeature.selectArchiveStats
  );
  protected readonly folders = this.store.selectSignal(
    archiveFeature.selectArchivedFolders
  );
  protected readonly rootDocuments = this.store.selectSignal(
    archiveFeature.selectRootDocuments
  );
  protected readonly isEmpty = this.store.selectSignal(
    archiveFeature.selectIsArchiveEmpty
  );
  protected readonly canEmpty = this.store.selectSignal(
    archiveFeature.selectCanEmptyArchive
  );

  // Computed signals for loading state
  protected readonly isLoading = computed(
    () => this.archive()?.state === 'loading'
  );

  // Tree view state
  expandedFolders = signal(new Set<string>());

  restoreFolder(folder: ArchivedFolderWithChildren) {
    this.store.dispatch(
      ArchiveActions.openRestoreFolderModalCommand({ folder })
    );
  }

  restoreDocument(doc: ArchivedDocument) {
    this.store.dispatch(
      ArchiveActions.openRestoreDocumentModalCommand({ document: doc })
    );
  }

  deleteFolder(folder: ArchivedFolderWithChildren) {
    this.store.dispatch(
      ArchiveActions.openDeleteFolderModalCommand({ folder })
    );
  }

  deleteDocument(doc: ArchivedDocument) {
    this.store.dispatch(
      ArchiveActions.openDeleteDocumentModalCommand({ document: doc })
    );
  }

  emptyArchive() {
    this.store.dispatch(ArchiveActions.openEmptyArchiveModalCommand());
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
}
