import {
  Component,
  ChangeDetectionStrategy,
  inject,
  HostListener,
  signal,
  effect,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  trigger,
  style,
  transition,
  animate,
  state,
} from '@angular/animations';
import { FolderSidebarComponent } from './folders/components/folder-sidebar.component';
import { DocumentListComponent } from './documents/components/document-list.component';
import { DocumentDeleteDialogComponent } from './documents/components/document-delete-dialog.component';
import { FolderDialogComponent } from './folders/components/folder-dialog.component';
import { FolderDeleteDialogComponent } from './folders/components/folder-delete-dialog.component';
import { UIStore } from '../shared/ui.store';
import { LibraryStore } from './library.store';

@Component({
  selector: 'app-library-shell',
  standalone: true,
  imports: [
    CommonModule,
    FolderSidebarComponent,
    DocumentListComponent,
    DocumentDeleteDialogComponent,
    FolderDialogComponent,
    FolderDeleteDialogComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [
    trigger('sidebarAnimation', [
      state(
        'in',
        style({
          width: '16rem',
          opacity: 1,
        })
      ),
      state(
        'out',
        style({
          width: '0',
          opacity: 0,
        })
      ),
      transition('in => out', [animate('300ms cubic-bezier(0.4, 0, 0.2, 1)')]),
      transition('out => in', [animate('300ms cubic-bezier(0.4, 0, 0.2, 1)')]),
    ]),
    trigger('fadeInOut', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('300ms ease-in', style({ opacity: 1 })),
      ]),
      transition(':leave', [animate('300ms ease-out', style({ opacity: 0 }))]),
    ]),
    trigger('fadeScaleIn', [
      transition(':enter', [
        style({ transform: 'scale(0.95)', opacity: 0 }),
        animate(
          '300ms cubic-bezier(0.4, 0, 0.2, 1)',
          style({ transform: 'scale(1)', opacity: 1 })
        ),
      ]),
      transition(':leave', [
        animate(
          '300ms cubic-bezier(0.4, 0, 0.2, 1)',
          style({ transform: 'scale(0.95)', opacity: 0 })
        ),
      ]),
    ]),
  ],
  template: `
    <div class="h-screen flex overflow-hidden bg-background">
      <!-- Main Content Area -->
      <div class="flex-1 flex overflow-hidden relative">
        <!-- Desktop Sidebar -->
        <div
          class="hidden sm:block absolute inset-y-0 left-0 z-10 transition-all duration-300 ease-in-out border-r border-border bg-muted/5"
          [class.w-64]="!uiStore.sidebarCollapsed()"
          [class.w-14]="uiStore.sidebarCollapsed()"
        >
          <app-folder-sidebar
            [collapsed]="uiStore.sidebarCollapsed()"
            class="h-full"
          />
        </div>

        <!-- Mobile Sidebar Overlay -->
        @if (!uiStore.sidebarCollapsed() && isMobile()) {
        <div
          @fadeInOut
          class="fixed inset-0 bg-black/50 z-40 sm:hidden"
          (click)="toggleSidebar()"
          (keydown.escape)="toggleSidebar()"
          tabindex="0"
          role="button"
          aria-label="Close sidebar"
        ></div>
        <div
          @fadeScaleIn
          class="fixed left-0 top-0 h-full w-64 bg-background shadow-xl z-50 sm:hidden"
        >
          <app-folder-sidebar [collapsed]="false" class="h-full" />
        </div>
        }

        <!-- Right Content - Documents -->
        <div
          class="flex-1 transition-all duration-300 ease-in-out"
          [class.sm:ml-64]="!uiStore.sidebarCollapsed()"
          [class.sm:ml-14]="uiStore.sidebarCollapsed()"
          [class.ml-0]="isMobile()"
        >
          <app-document-list class="h-full" />
        </div>
      </div>
    </div>

    <!-- Dialogs -->
    <app-document-delete-dialog />
    <app-folder-dialog />
    <app-folder-delete-dialog />
  `,
})
export class LibraryShellComponent {
  protected uiStore = inject(UIStore);
  protected libraryStore = inject(LibraryStore);
  protected isMobile = signal(false);

  constructor() {
    // Check if mobile on initialization
    this.checkIfMobile();

    // Auto-close sidebar on mobile when window resizes
    effect(() => {
      if (this.isMobile() && !this.uiStore.sidebarCollapsed()) {
        // Don't close on initial load, only on resize
      }
    });
  }

  toggleSidebar() {
    this.uiStore.toggleSidebar();
  }

  @HostListener('window:resize')
  onResize() {
    this.checkIfMobile();
    // Auto-close sidebar when switching to mobile
    if (this.isMobile() && !this.uiStore.sidebarCollapsed()) {
      this.uiStore.toggleSidebar();
    }
  }

  @HostListener('window:keydown', ['$event'])
  handleKeyboardEvent(event: KeyboardEvent) {
    // Toggle sidebar with Ctrl/Cmd + B
    if ((event.ctrlKey || event.metaKey) && event.key === 'b') {
      event.preventDefault();
      this.toggleSidebar();
    }
  }

  private checkIfMobile() {
    this.isMobile.set(window.innerWidth < 640); // sm breakpoint
  }
}
