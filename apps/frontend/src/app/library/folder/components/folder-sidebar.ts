import {
  Component,
  inject,
  ChangeDetectionStrategy,
  signal,
  effect,
  HostListener,
} from '@angular/core';

import { RouterLink, RouterLinkActive } from '@angular/router';
import { FolderTree } from './folder-tree';
import { UIStore } from '../../../shared/ui.store';
import { FolderItem } from '../store/state/folder-item';
import { FolderTree as Folder } from '../store/state/folder-tree';
import { Store } from '@ngrx/store';
import { folderFeature } from '../store/folder.feature';
import { FolderActions } from '../store/folder.actions';
import { DocumentActions } from '../../documents/store/document.actions';
import { DocumentListItem } from '../../documents/store/state/document';
import { UnwrapAsyncDataPipe } from '../../../core/pipes/unwrapAsyncData';
import { QueryAsyncStatePipe } from '../../../core/pipes/queryAsyncState';
import { AsyncDataItem } from '../../../core/utils/async-data-item';
import { distinctUntilChanged, Subject, throttleTime } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

@Component({
  selector: 'app-folder-sidebar',
  standalone: true,
  imports: [
    FolderTree,
    RouterLink,
    RouterLinkActive,
    UnwrapAsyncDataPipe,
    QueryAsyncStatePipe,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      class="h-full flex flex-col glass border-r border-border/50 transition-all duration-200"
      [class.items-center]="uiStore.sidebarCollapsed()"
      [class.sidebar-collapsed]="uiStore.sidebarCollapsed()"
      [class.sidebar-expanded]="!uiStore.sidebarCollapsed()"
    >
      <!-- Top section with new folder button -->
      <div class="p-4 pb-2">
        @if (uiStore.sidebarCollapsed()) {
        <!-- Expand button at the top when collapsed -->
        <button
          (click)="toggleSidebar()"
          class="w-10 h-10 mb-2 flex items-center justify-center hover:bg-muted rounded-lg transition-colors"
          title="Expand sidebar"
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
        } @else if (isMobile()) {
        <!-- Close button for mobile -->
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold">Folders</h2>
          <button
            (click)="toggleSidebar()"
            class="p-2 hover:bg-muted rounded-lg transition-colors sm:hidden"
            title="Close sidebar"
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
        }

        <!-- Top Actions -->
        <div
          class="flex items-center"
          [class.justify-center]="uiStore.sidebarCollapsed()"
          [class.gap-2]="!uiStore.sidebarCollapsed()"
        >
          <!-- New Folder Button -->
          <button
            (click)="showNewFolderDialog()"
            [class.flex-1]="!uiStore.sidebarCollapsed()"
            [class.w-10]="uiStore.sidebarCollapsed()"
            [class.h-10]="uiStore.sidebarCollapsed()"
            [class.gap-2]="!uiStore.sidebarCollapsed()"
            class="flex items-center justify-center px-3 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
            [title]="uiStore.sidebarCollapsed() ? 'New Folder' : ''"
          >
            <svg
              class="w-4 h-4 flex-shrink-0"
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
            <span class="sidebar-label">New Folder</span>
          </button>

          <!-- Expand/Collapse Toggle -->
          @if (!uiStore.sidebarCollapsed()) {
          <button
            (click)="toggleSidebar()"
            class="p-2 hover:bg-muted rounded-lg transition-colors"
            title="Collapse sidebar"
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
                d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
              />
            </svg>
          </button>
          }
        </div>
      </div>
      @let folderData = asyncFolders() | unwrapAsyncData; @let folderState =
      asyncFolders() | queryAsyncState;

      <!-- Middle scrollable section -->
      <div class="flex-1 overflow-y-auto p-2">
        <!-- Loading State -->
        @if (folderState.isLoading) {
        <div class="flex items-center justify-center py-8">
          <div
            class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"
          ></div>
        </div>
        }

        <!-- Error State -->
        @else if (folderState.isError) {
        <div class="text-center py-8 px-4">
          <p class="text-sm text-error">Failed to load folders</p>
          <p class="text-xs text-muted-foreground mt-1">
            {{ asyncFolders().error }}
          </p>
        </div>
        }

        <!-- Loaded State -->
        @else if (folderState.isLoaded) {
        <!-- All Documents -->
        <a
          routerLink="/library"
          [queryParams]="{}"
          routerLinkActive="bg-muted text-primary-600"
          [routerLinkActiveOptions]="{ exact: true }"
          [class.w-full]="!uiStore.sidebarCollapsed()"
          [class.w-10]="uiStore.sidebarCollapsed()"
          [class.h-10]="uiStore.sidebarCollapsed()"
          [class.justify-center]="uiStore.sidebarCollapsed()"
          class="flex items-center px-3 py-2 text-sm font-medium text-foreground hover:bg-muted rounded-lg transition-colors mb-1"
          [class.gap-2]="!uiStore.sidebarCollapsed()"
          [title]="
            uiStore.sidebarCollapsed()
              ? 'All Documents (' + folderData.totalDocumentCount + ')'
              : ''
          "
        >
          <svg
            class="w-4 h-4 flex-shrink-0"
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
          <span class="sidebar-label flex-1 text-left">
            All Documents
            <span class="text-xs text-muted-foreground font-normal">
              ({{ folderData.totalDocumentCount }})
            </span>
          </span>
        </a>

        <!-- Unfiled Documents -->
        <a
          routerLink="/library"
          [queryParams]="{ folderId: 'unfiled' }"
          routerLinkActive="bg-muted text-primary-600"
          [class.w-full]="!uiStore.sidebarCollapsed()"
          [class.w-10]="uiStore.sidebarCollapsed()"
          [class.h-10]="uiStore.sidebarCollapsed()"
          [class.justify-center]="uiStore.sidebarCollapsed()"
          class="flex items-center px-3 py-2 text-sm font-medium text-foreground hover:bg-muted rounded-lg transition-colors mb-1"
          [class.gap-2]="!uiStore.sidebarCollapsed()"
          [title]="
            uiStore.sidebarCollapsed()
              ? 'Unfiled (' + folderData.unfiledCount + ')'
              : ''
          "
        >
          <svg
            class="w-4 h-4 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
            />
          </svg>
          <span class="sidebar-label flex-1 text-left">
            Unfiled
            <span class="text-xs text-muted-foreground font-normal">
              ({{ folderData.unfiledCount }})
            </span>
          </span>
        </a>

        <!-- Archive -->
        <a
          routerLink="/library/archive"
          routerLinkActive="bg-muted text-primary-600"
          [class.w-full]="!uiStore.sidebarCollapsed()"
          [class.w-10]="uiStore.sidebarCollapsed()"
          [class.h-10]="uiStore.sidebarCollapsed()"
          [class.justify-center]="uiStore.sidebarCollapsed()"
          class="flex items-center px-3 py-2 text-sm font-medium text-foreground hover:bg-muted rounded-lg transition-colors mb-4"
          [class.gap-2]="!uiStore.sidebarCollapsed()"
          [title]="uiStore.sidebarCollapsed() ? 'Archive' : ''"
          [class.bg-error-100]="dragOverArchive()"
          [class.dark:bg-error-900]="dragOverArchive()"
          [class.scale-[1.02]]="dragOverArchive()"
          [class.shadow-lg]="dragOverArchive()"
          [class.border-2]="dragOverArchive()"
          [class.border-error-500]="dragOverArchive()"
          [class.border-dashed]="dragOverArchive()"
          (drop)="onDropToArchive($event)"
          (dragover)="onDragOverArchive($event)"
          (dragleave)="onDragLeaveArchive($event)"
          (dragenter)="onDragEnterArchive($event)"
        >
          <svg
            class="w-4 h-4 flex-shrink-0"
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
          <span class="sidebar-label flex-1 text-left">Archive</span>
        </a>

        <!-- User Folders -->
        @if (!contentCollapsed()) {
        <div class="space-y-1">
          @for (folder of folderData.folders; track folder.id) {
          <app-folder-tree
            [folders]="[folder]"
            [selectedFolderId]="selectedFolderId()"
            [expandedFolders]="expandedFolders()"
            [dragOverFolder]="dragOverFolder()"
            (folderToggled)="toggleFolderExpanded($event)"
            (folderEdit)="editFolder($event.folder, $event.event)"
            (folderDelete)="deleteFolder($event.folder, $event.event)"
            (folderDrop)="onDropToFolder($event.event, $event.folder)"
            (folderDragOver)="onDragOver($event.event, $event.folder)"
            (folderDragLeave)="onDragLeave()"
          />
          }
        </div>
        } @else {
        <!-- Collapsed folder icons -->
        <div class="space-y-1">
          @for (folder of folderData.folders; track folder.id) {
          <div
            (mouseenter)="onFolderHover(folder.id)"
            (mouseleave)="onFolderLeave()"
          >
            <a
              routerLink="/library"
              [queryParams]="{ folderId: folder.id }"
              routerLinkActive="bg-muted text-primary-600"
              class="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-muted transition-colors relative"
              [title]="folder.name + ' (' + folder.documentCount + ')'"
            >
              <svg
                class="w-4 h-4"
                [style.color]="folder.color || 'currentColor'"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"
                ></path>
              </svg>
              @if (folder.children.length > 0) {
              <span
                class="absolute -top-1 -right-1 w-2 h-2 bg-primary-600 rounded-full"
              ></span>
              }
            </a>

            <!-- Show child folders when hovering -->
            @if (hoveredFolderId() === folder.id && folder.children.length > 0)
            {
            <div class="ml-2 mt-1 space-y-1 animate-in">
              @for (child of folder.children; track child.id) {
              <a
                routerLink="/library"
                [queryParams]="{ folderId: child.id }"
                routerLinkActive="bg-muted text-primary-600"
                class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-muted transition-colors"
                [title]="child.name + ' (' + child.documentCount + ')'"
              >
                <svg
                  class="w-3 h-3"
                  [style.color]="child.color || 'currentColor'"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"
                  ></path>
                </svg>
              </a>
              }
            </div>
            }
          </div>
          }
        </div>
        } }
      </div>
    </div>
  `,
  styles: [
    `
      /* Smooth transitions for sidebar expansion/collapse */
      .sidebar-label {
        display: inline-block;
        overflow: hidden;
        white-space: nowrap;
        transition: max-width 300ms cubic-bezier(0.4, 0, 0.2, 1),
          opacity 250ms cubic-bezier(0.4, 0, 0.2, 1),
          margin 300ms cubic-bezier(0.4, 0, 0.2, 1);
        max-width: 200px;
      }

      .sidebar-collapsed .sidebar-label {
        max-width: 0;
        opacity: 0;
        margin-left: 0;
        margin-right: 0;
        transition: max-width 300ms cubic-bezier(0.4, 0, 0.2, 1),
          opacity 150ms cubic-bezier(0.4, 0, 0.2, 1),
          margin 300ms cubic-bezier(0.4, 0, 0.2, 1);
      }

      .sidebar-expanded .sidebar-label {
        max-width: 200px;
        opacity: 1;
        transition-delay: 150ms; /* Delay appearance on expand */
      }

      /* Container styles */
      .sidebar-collapsed {
        width: 100%;
      }

      .sidebar-expanded {
        width: 100%;
      }

      /* Hover expansion animation */
      @keyframes fadeIn {
        from {
          opacity: 0;
          transform: translateY(-4px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      .animate-in {
        animation: fadeIn 0.2s ease-out;
      }
    `,
  ],
})
export class FolderSidebar {
  protected uiStore = inject(UIStore);
  private readonly store = inject(Store);

  // Delayed collapsed state for content switching
  protected contentCollapsed = signal(this.uiStore.sidebarCollapsed());

  // Mobile detection
  protected isMobile = signal(false);

  // Track which folder is being hovered in collapsed mode
  protected hoveredFolderId = signal<string | null>(null);

  // Track drag over archive
  protected dragOverArchive = signal(false);

  private onDragSubject$ = new Subject<string | undefined>();

  constructor() {
    // Check if mobile on initialization
    this.checkIfMobile();

    // Update content collapsed state with delay
    effect(() => {
      const isCollapsed = this.uiStore.sidebarCollapsed();
      this.contentCollapsed.set(isCollapsed);
    });

    this.onDragSubject$
      .pipe(takeUntilDestroyed(), throttleTime(300), distinctUntilChanged())
      .subscribe((folderId) => {
        this.store.dispatch(
          FolderActions.setDragOverFolderCommand({ folderId })
        );
      });
  }

  private checkIfMobile() {
    this.isMobile.set(window.innerWidth < 640);
  }

  @HostListener('window:resize')
  onResize() {
    this.checkIfMobile();
  }

  asyncFolders = this.store.selectSignal<AsyncDataItem<Folder>>(
    folderFeature.selectFolder
  );
  selectedFolderId = this.store.selectSignal(
    folderFeature.selectSelectedFolderId
  );
  expandedFolders = this.store.selectSignal(
    folderFeature.selectExpandedFolders
  );
  dragOverFolder = this.store.selectSignal(folderFeature.selectDragOverFolder);

  toggleFolderExpanded(folderId: string) {
    this.store.dispatch(
      FolderActions.toggleFolderExpandedCommand({ folderId })
    );
  }

  showNewFolderDialog() {
    this.store.dispatch(FolderActions.openCreateFolderModalCommand({}));
  }

  editFolder(folder: FolderItem, event: Event) {
    event.stopPropagation();
    this.store.dispatch(FolderActions.openEditFolderModalCommand({ folder }));
  }

  deleteFolder(folder: FolderItem, event: Event) {
    event.stopPropagation();
    this.store.dispatch(FolderActions.openDeleteFolderModalCommand({ folder }));
  }

  onDropToFolder(event: DragEvent, folder: FolderItem) {
    event.preventDefault();
    event.stopPropagation();
    this.store.dispatch(
      FolderActions.setDragOverFolderCommand({ folderId: undefined })
    );
    const documentId = event.dataTransfer?.getData('documentId');
    const folderId = event.dataTransfer?.getData('folderId') || undefined;
    if (documentId) {
      this.store.dispatch(
        FolderActions.addDocumentsToFolderCommand({
          from: folderId,
          to: folder.id,
          documentId,
        })
      );
    }
  }

  onDragOver(event: DragEvent, folder: FolderItem) {
    event.preventDefault();
    this.onDragSubject$.next(folder.id);
  }

  onDragLeave() {
    this.onDragSubject$.next(undefined);
  }

  toggleSidebar() {
    this.uiStore.toggleSidebar();
  }

  onFolderHover(folderId: string) {
    if (this.uiStore.sidebarCollapsed()) {
      this.hoveredFolderId.set(folderId);
    }
  }

  onFolderLeave() {
    this.hoveredFolderId.set(null);
  }

  onDropToArchive(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.dragOverArchive.set(false);
    
    const documentId = event.dataTransfer?.getData('documentId');
    const filename = event.dataTransfer?.getData('text/plain') || 'Document';
    
    if (documentId) {
      // We'll create a minimal document object to pass to the delete modal
      // The modal will show the filename we have
      this.store.dispatch(
        DocumentActions.openDeleteDocumentModalCommand({
          document: {
            id: documentId,
            documentId: documentId,
            filename: filename,
            folderId: event.dataTransfer?.getData('folderId') || undefined,
          } as DocumentListItem
        })
      );
    }
  }

  onDragOverArchive(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.dragOverArchive.set(true);
  }

  onDragLeaveArchive(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.dragOverArchive.set(false);
  }

  onDragEnterArchive(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.dragOverArchive.set(true);
  }
}
