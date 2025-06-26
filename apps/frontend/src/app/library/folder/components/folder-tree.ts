import {
  Component,
  ChangeDetectionStrategy,
  input,
  output,
} from '@angular/core';

import {
  trigger,
  style,
  transition,
  animate,
  state,
} from '@angular/animations';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { FolderItem } from '../store/state/folder-item';

@Component({
  selector: 'app-folder-tree',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [
    trigger('expandCollapse', [
      transition(':enter', [
        style({
          height: '0',
          opacity: '0',
          overflow: 'hidden',
          transform: 'translateY(-10px)',
        }),
        animate(
          '300ms cubic-bezier(0.4, 0, 0.2, 1)',
          style({
            height: '*',
            opacity: '1',
            overflow: 'visible',
            transform: 'translateY(0)',
          })
        ),
      ]),
      transition(':leave', [
        style({
          height: '*',
          opacity: '1',
          overflow: 'hidden',
          transform: 'translateY(0)',
        }),
        animate(
          '250ms cubic-bezier(0.4, 0, 0.2, 1)',
          style({
            height: '0',
            opacity: '0',
            overflow: 'hidden',
            transform: 'translateY(-10px)',
          })
        ),
      ]),
    ]),
    trigger('chevronRotate', [
      state('collapsed', style({ transform: 'rotate(0deg)' })),
      state('expanded', style({ transform: 'rotate(180deg)' })),
      transition(
        'collapsed <=> expanded',
        animate('250ms cubic-bezier(0.4, 0, 0.2, 1)')
      ),
    ]),
    trigger('fadeIn', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('150ms ease-in', style({ opacity: 1 })),
      ]),
    ]),
  ],
  template: `
    @for (folder of folders(); track folder.id; let i = $index) {
    <div @fadeIn [style.animation-delay.ms]="i * 50" class="folder-item">
      <!-- Folder Row Container -->
      <div class="relative group/folder">
        @if (folder.children && folder.children.length > 0) {
        <button
          (click)="folderToggled.emit(folder.id); $event.stopPropagation()"
          (keydown.enter)="folderToggled.emit(folder.id)"
          (keydown.space)="folderToggled.emit(folder.id)"
          class="absolute left-0 top-1/2 -translate-y-1/2 p-2 hover:bg-muted/50 rounded z-20 transition-all duration-200"
          [attr.aria-label]="'Toggle folder ' + folder.name"
          [attr.aria-expanded]="expandedFolders().includes(folder.id)"
        >
          <svg
            [@chevronRotate]="
              expandedFolders().includes(folder.id) ? 'expanded' : 'collapsed'
            "
            class="w-4 h-4 text-muted-foreground"
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
        </button>
        }
        <a
          [routerLink]="['/library', folder.id]"
          routerLinkActive="bg-muted text-primary-600"
          class="w-full flex items-center gap-2 px-3 py-2 pl-8 pr-16 text-sm font-medium text-foreground hover:bg-muted rounded-lg transition-all duration-200 cursor-pointer hover:shadow-sm"
          [class.bg-primary-100]="dragOverFolder() === folder.id"
          [class.dark:bg-primary-900]="dragOverFolder() === folder.id"
          [class.scale-[1.02]]="dragOverFolder() === folder.id"
          [class.shadow-lg]="dragOverFolder() === folder.id"
          [class.border-2]="dragOverFolder() === folder.id"
          [class.border-primary-500]="dragOverFolder() === folder.id"
          [class.border-dashed]="dragOverFolder() === folder.id"
          (drop)="onDrop($event, folder)"
          (dragover)="onDragOver($event, folder)"
          (dragleave)="onDragLeave($event)"
          (dragenter)="onDragEnter($event, folder)"
        >
          <svg
            class="w-4 h-4 flex-shrink-0"
            [style.color]="folder.color || 'currentColor'"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"
            ></path>
          </svg>

          <span class="flex-1 text-left truncate">
            {{ folder.name }}
            <span class="text-xs text-muted-foreground font-normal">
              ({{ folder.documentCount }})
            </span>
          </span>
        </a>

        <!-- Folder Actions -->
        <div
          class="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover/folder:opacity-100 flex items-center gap-1 transition-opacity duration-200 z-30 bg-background/90 backdrop-blur-sm rounded-md px-1"
        >
          <button
            (click)="
              folderEdit.emit({ folder: folder, event: $event });
              $event.stopPropagation()
            "
            (keydown.enter)="folderEdit.emit({ folder: folder, event: $event })"
            (keydown.space)="folderEdit.emit({ folder: folder, event: $event })"
            class="p-1 hover:bg-muted rounded transition-all duration-150 hover:scale-110"
            title="Edit folder"
          >
            <svg
              class="w-3 h-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
              />
            </svg>
          </button>
          <button
            (click)="
              folderDelete.emit({ folder: folder, event: $event });
              $event.stopPropagation()
            "
            (keydown.enter)="
              folderDelete.emit({ folder: folder, event: $event })
            "
            (keydown.space)="
              folderDelete.emit({ folder: folder, event: $event })
            "
            class="p-1 hover:bg-error/20 hover:text-error rounded transition-all duration-150 hover:scale-110"
            title="Delete folder"
          >
            <svg
              class="w-3 h-3"
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
          </button>
        </div>
      </div>

      <!-- Nested Folders -->
      @if (folder.children && folder.children.length > 0 &&
      expandedFolders().includes(folder.id)) {
      <div @expandCollapse class="ml-4 origin-top">
        <app-folder-tree
          @fadeIn
          [folders]="folder.children"
          [selectedFolderId]="selectedFolderId()"
          [expandedFolders]="expandedFolders()"
          [dragOverFolder]="dragOverFolder()"
          (folderToggled)="folderToggled.emit($event)"
          (folderEdit)="folderEdit.emit($event)"
          (folderDelete)="folderDelete.emit($event)"
          (folderDrop)="folderDrop.emit($event)"
          (folderDragOver)="folderDragOver.emit($event)"
          (folderDragLeave)="folderDragLeave.emit()"
        />
      </div>
      }
    </div>
    }
  `,
})
export class FolderTree {
  // Input signals
  folders = input<FolderItem[]>([]);
  selectedFolderId = input<string | undefined>(undefined);
  expandedFolders = input<string[]>([]);
  dragOverFolder = input<string | undefined>(undefined);

  // Output signals
  folderToggled = output<string>();
  folderEdit = output<{
    folder: FolderItem;
    event: Event;
  }>();
  folderDelete = output<{
    folder: FolderItem;
    event: Event;
  }>();
  folderDrop = output<{
    event: DragEvent;
    folder: FolderItem;
  }>();
  folderDragOver = output<{
    event: DragEvent;
    folder: FolderItem;
  }>();
  folderDragLeave = output<void>();

  onDrop(event: DragEvent, folder: FolderItem) {
    event.preventDefault();
    event.stopPropagation();
    this.folderDrop.emit({ event, folder });
  }

  onDragOver(event: DragEvent, folder: FolderItem) {
    event.preventDefault();
    event.stopPropagation();
    this.folderDragOver.emit({ event, folder });
  }

  onDragLeave(event: DragEvent) {
    event.stopPropagation();
    this.folderDragLeave.emit();
  }

  onDragEnter(event: DragEvent, folder: FolderItem) {
    event.preventDefault();
    event.stopPropagation();
    this.folderDragOver.emit({ event, folder });
  }
}
