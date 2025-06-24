import {
  Component,
  inject,
  ChangeDetectionStrategy,
  signal,
  effect,
} from '@angular/core';

import { RouterLink, RouterLinkActive } from '@angular/router';
import { FolderTree } from './folder-tree';
import { UIStore } from '../../../shared/ui.store';
import { Folder, FolderItem } from '../store/state/folder';
import { Store } from '@ngrx/store';
import { folderFeature } from '../store/folder.feature';
import { FolderActions } from '../store/folder.actions';
import { UnwrapAsyncDataPipe } from '../../../core/pipes/unwrapAsyncData';
import { QueryAsyncStatePipe } from '../../../core/pipes/queryAsyncState';
import { AsyncDataItem } from '../../../core/utils/async-data-item';

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
            (folderSelected)="selectFolder($event)"
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
          @for (folder of folderData.folders; track folder.id; let i = $index) {
          @if (i < 3) {
          <a
            routerLink="/library"
            [queryParams]="{ folderId: folder.id }"
            routerLinkActive="bg-muted text-primary-600"
            class="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-muted transition-colors"
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
          </a>
          } } @if (folderData.folders.length > 3) {
          <button
            class="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-muted transition-colors text-muted-foreground"
            title="{{ folderData.folders.length - 3 }} more folders"
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
                d="M5 12h.01M12 12h.01M19 12h.01M6 12a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0z"
              />
            </svg>
          </button>
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
    `,
  ],
})
export class FolderSidebar {
  protected uiStore = inject(UIStore);
  private readonly store = inject(Store);

  // Delayed collapsed state for content switching
  protected contentCollapsed = signal(this.uiStore.sidebarCollapsed());

  private timeoutId: number | null = null;

  constructor() {
    // Update content collapsed state with delay
    effect(() => {
      const isCollapsed = this.uiStore.sidebarCollapsed();

      // Clear any pending timeout
      if (this.timeoutId) {
        clearTimeout(this.timeoutId);
        this.timeoutId = null;
      }

      if (isCollapsed) {
        // Delay content switch when collapsing - wait for full animation
        this.timeoutId = setTimeout(() => {
          this.contentCollapsed.set(true);
        }, 300) as unknown as number; // Match animation duration exactly
      } else {
        // Switch content immediately when expanding
        this.contentCollapsed.set(false);
      }
    });
  }

  // NGRX store selectors
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

  selectFolder(folderId: string | null) {
    this.store.dispatch(FolderActions.selectFolderCommand({ folderId }));
  }

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
    // const documentId = event.dataTransfer?.getData('documentId');
    // if (documentId) {
    //   this.store.dispatch(
    //     LibraryActions.addDocumentsToFolderCommand({
    //       folderId: folder.id,
    //       documentIds: [documentId],
    //     })
    //   );
    // }
  }

  onDragOver(event: DragEvent, folder: FolderItem) {
    event.preventDefault();
    this.store.dispatch(
      FolderActions.setDragOverFolderCommand({ folderId: folder.id })
    );
  }

  onDragLeave() {
    this.store.dispatch(
      FolderActions.setDragOverFolderCommand({ folderId: null })
    );
  }

  toggleSidebar() {
    this.uiStore.toggleSidebar();
  }
}
