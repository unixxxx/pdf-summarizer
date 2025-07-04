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
import { UIStore } from '../shared/ui.store';
import { Store } from '@ngrx/store';
import { documentFeature } from './documents/store/document.feature';

@Component({
  selector: 'app-library-shell',
  standalone: true,
  imports: [RouterOutlet, FolderSidebar],
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
          [style.margin-left.rem]="
            !isMobile() ? (uiStore.sidebarCollapsed() ? 3.5 : 16) : 0
          "
        >
          <router-outlet class="h-full" />
        </div>
      </div>
    </div>
  `,
})
export class LibraryShell {
  protected uiStore = inject(UIStore);
  protected isMobile = signal(false);

  constructor() {
    // Check if mobile on initialization
    this.checkIfMobile();

    // Set initial sidebar state based on device type
    if (this.isMobile()) {
      this.uiStore.setSidebarCollapsed(true);
    }
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
