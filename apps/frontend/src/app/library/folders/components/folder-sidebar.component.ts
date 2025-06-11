import {
  Component,
  inject,
  ChangeDetectionStrategy,
  input,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { LibraryStore } from '../../library.store';
import { FolderTreeComponent } from './folder-tree.component';
import { FolderWithChildren } from '../folder.model';
import { UIStore } from '../../../shared/ui.store';

@Component({
  selector: 'app-folder-sidebar',
  standalone: true,
  imports: [CommonModule, FolderTreeComponent, RouterLink, RouterLinkActive],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="h-full flex flex-col bg-background" [class.items-center]="collapsed()">
      <!-- Top section with new folder button -->
      <div class="p-4 pb-2 border-b border-border">
        @if (collapsed()) {
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
          [class.justify-center]="collapsed()"
          [class.gap-2]="!collapsed()"
        >
          <!-- New Folder Button -->
          <button
            (click)="showNewFolderDialog()"
            [class.flex-1]="!collapsed()"
            [class.w-10]="collapsed()"
            [class.h-10]="collapsed()"
            class="flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
            [title]="collapsed() ? 'New Folder' : ''"
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
            @if (!collapsed()) {
            <span>New Folder</span>
            }
          </button>

          <!-- Expand/Collapse Toggle -->
          @if (!collapsed()) {
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

      <!-- Middle scrollable section -->
      <div class="flex-1 overflow-y-auto p-2">
        <!-- All Documents -->
        <button
          (click)="selectFolder(null)"
          [class.bg-muted]="!libraryStore.selectedFolderId()"
          [class.text-primary-600]="!libraryStore.selectedFolderId()"
          [class.w-full]="!collapsed()"
          [class.w-10]="collapsed()"
          [class.h-10]="collapsed()"
          [class.justify-center]="collapsed()"
          class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-foreground hover:bg-muted rounded-lg transition-colors mb-1"
          [title]="
            collapsed()
              ? 'All Documents (' + libraryStore.totalDocumentCount() + ')'
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
          @if (!collapsed()) {
          <span class="flex-1 text-left">
            All Documents
            <span class="text-xs text-muted-foreground font-normal">
              ({{ libraryStore.totalDocumentCount() }})
            </span>
          </span>
          }
        </button>

        <!-- Unfiled Documents -->
        <button
          (click)="selectFolder('unfiled')"
          [class.bg-muted]="libraryStore.selectedFolderId() === 'unfiled'"
          [class.text-primary-600]="
            libraryStore.selectedFolderId() === 'unfiled'
          "
          [class.w-full]="!collapsed()"
          [class.w-10]="collapsed()"
          [class.h-10]="collapsed()"
          [class.justify-center]="collapsed()"
          class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-foreground hover:bg-muted rounded-lg transition-colors mb-1"
          [title]="
            collapsed() ? 'Unfiled (' + libraryStore.unfiledCount() + ')' : ''
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
          @if (!collapsed()) {
          <span class="flex-1 text-left">
            Unfiled
            <span class="text-xs text-muted-foreground font-normal">
              ({{ libraryStore.unfiledCount() }})
            </span>
          </span>
          }
        </button>

        <!-- Trash -->
        <a
          routerLink="/app/library/trash"
          routerLinkActive="bg-muted text-primary-600"
          [class.w-full]="!collapsed()"
          [class.w-10]="collapsed()"
          [class.h-10]="collapsed()"
          [class.justify-center]="collapsed()"
          class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-foreground hover:bg-muted rounded-lg transition-colors mb-4"
          [title]="collapsed() ? 'Trash' : ''"
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
          @if (!collapsed()) {
          <span class="flex-1 text-left">Trash</span>
          }
        </a>

        <!-- User Folders -->
        @if (!collapsed()) {
        <div class="space-y-1">
          @for (folder of libraryStore.folders(); track folder.id) {
          <app-folder-tree
            [folders]="[folder]"
            [selectedFolderId]="libraryStore.selectedFolderId()"
            [expandedFolders]="libraryStore.expandedFolders()"
            [dragOverFolder]="libraryStore.dragOverFolder()"
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
          @for (folder of libraryStore.folders(); track folder.id; let i =
          $index) { @if (i < 3) {
          <button
            (click)="selectFolder(folder.id)"
            [class.bg-muted]="libraryStore.selectedFolderId() === folder.id"
            [class.text-primary-600]="
              libraryStore.selectedFolderId() === folder.id
            "
            class="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-muted transition-colors"
            [title]="
              folder.name +
              ' (' +
              (folder.documentCount || folder.document_count || 0) +
              ')'
            "
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
          </button>
          } } @if (libraryStore.folders().length > 3) {
          <button
            class="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-muted transition-colors text-muted-foreground"
            title="{{ libraryStore.folders().length - 3 }} more folders"
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
        }
      </div>
    </div>
  `,
})
export class FolderSidebarComponent {
  protected libraryStore = inject(LibraryStore);
  protected uiStore = inject(UIStore);

  collapsed = input<boolean>(false);

  selectFolder(folderId: string | null) {
    this.libraryStore.selectFolder(folderId);
  }

  toggleFolderExpanded(folderId: string) {
    this.libraryStore.toggleFolderExpanded(folderId);
  }

  showNewFolderDialog() {
    this.libraryStore.showNewFolderDialog();
  }

  editFolder(folder: FolderWithChildren, event: Event) {
    event.stopPropagation();
    this.libraryStore.showEditFolderDialog(folder);
  }

  deleteFolder(folder: FolderWithChildren, event: Event) {
    event.stopPropagation();
    this.libraryStore.confirmDeleteFolder(folder);
  }

  onDropToFolder(event: DragEvent, folder: FolderWithChildren) {
    event.preventDefault();
    const documentId = event.dataTransfer?.getData('documentId');
    if (documentId) {
      this.libraryStore.handleDrop(folder.id, documentId);
    }
  }

  onDragOver(event: DragEvent, folder: FolderWithChildren) {
    event.preventDefault();
    this.libraryStore.setDragOverFolder(folder.id);
  }

  onDragLeave() {
    this.libraryStore.setDragOverFolder(null);
  }

  toggleSidebar() {
    this.uiStore.toggleSidebar();
  }
}