import {
  Component,
  ChangeDetectionStrategy,
  inject,
  HostListener,
  signal,
  effect,
} from '@angular/core';

import {
  trigger,
  style,
  transition,
  animate,
  state,
} from '@angular/animations';
import { RouterOutlet } from '@angular/router';
import { FolderSidebar } from './folder/components/folder-sidebar';
import { DocumentDeleteDialogComponent } from './documents/components/document-delete-dialog.component';
import { UIStore } from '../shared/ui.store';
import { LibraryStore } from './library.store';

@Component({
  selector: 'app-library-shell',
  standalone: true,
  imports: [
    RouterOutlet,
    FolderSidebar,
    DocumentDeleteDialogComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [
    trigger('sidebarAnimation', [
      state(
        'in',
        style({
          width: '16rem',
        })
      ),
      state(
        'out',
        style({
          width: '3.5rem',
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
    <div class="h-screen flex overflow-hidden">
      <!-- Main Content Area -->
      <div class="flex-1 flex overflow-hidden relative">
        <!-- Desktop Sidebar -->
        <div
          class="hidden sm:block absolute inset-y-0 left-0 z-10 overflow-hidden"
          [@sidebarAnimation]="uiStore.sidebarCollapsed() ? 'out' : 'in'"
        >
          <app-folder-sidebar class="h-full" />
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
          <app-folder-sidebar class="h-full" />
        </div>
        }

        <!-- Right Content - Router Outlet -->
        <div
          class="flex-1 transition-all duration-300 ease-in-out"
          [style.margin-left.rem]="!isMobile() ? (uiStore.sidebarCollapsed() ? 3.5 : 16) : 0"
        >
          <router-outlet class="h-full" />
        </div>
      </div>
    </div>

    <!-- Dialogs -->
    <app-document-delete-dialog />

  `,
})
export class LibraryShell {
  protected uiStore = inject(UIStore);
  protected libraryStore = inject(LibraryStore);
  protected isMobile = signal(false);

  private previousProcessingIds = new Set<string>();

  constructor() {
    // Check if mobile on initialization
    this.checkIfMobile();

    // Auto-close sidebar on mobile when window resizes
    effect(() => {
      if (this.isMobile() && !this.uiStore.sidebarCollapsed()) {
        // Don't close on initial load, only on resize
      }
    });

    // Watch for processing completion
    effect(() => {
      const currentProcessingIds = new Set(
        this.libraryStore.processingDocumentIds()
      );

      // Check if any documents that were processing are no longer processing
      for (const id of this.previousProcessingIds) {
        if (!currentProcessingIds.has(id)) {
          // Document finished processing, refresh the list with a delay
          // to ensure backend has committed the status change
          setTimeout(() => {
            this.libraryStore.loadDocuments();
          }, 1000); // 1 second delay to ensure DB commit is complete
          break; // Only refresh once even if multiple documents finished
        }
      }

      // Update the previous set for next comparison
      this.previousProcessingIds = currentProcessingIds;
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

  onDocumentUploaded() {
    // Refresh the document list with a small delay to ensure backend has updated status
    setTimeout(() => {
      this.libraryStore.loadDocuments();
    }, 500);
  }
}
