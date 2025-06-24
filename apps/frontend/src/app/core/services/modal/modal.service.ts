import {
  Injectable,
  ComponentRef,
  inject,
  EnvironmentInjector,
  Injector,
  Type,
} from '@angular/core';
import { Overlay, OverlayConfig, OverlayRef } from '@angular/cdk/overlay';
import { ComponentPortal } from '@angular/cdk/portal';
import { ModalConfig, ModalRef } from './modal.types';
import { ModalRefImpl, MODAL_REF } from './modal-ref';

@Injectable({
  providedIn: 'root',
})
export class ModalService {
  private overlay = inject(Overlay);
  private injector = inject(EnvironmentInjector);
  private modalCount = 0;
  private activeModals = new Map<string, ModalRefImpl<unknown>>();

  /**
   * Create and present a modal
   * @param config Modal configuration with component and optional inputs/outputs
   * @returns Promise that resolves to a typed ModalRef
   */
  async create<R = unknown, T extends Type<unknown> = Type<unknown>>(
    config: ModalConfig<T>
  ): Promise<ModalRef<R>> {
    const modalId = config.id || `modal-${++this.modalCount}`;

    // Create overlay
    const overlayRef = this.createOverlay(config);

    // Create modal ref
    const modalRef = new ModalRefImpl<R>(modalId, overlayRef);
    this.activeModals.set(modalId, modalRef as ModalRefImpl<unknown>);

    // Create component
    this.attachComponent(overlayRef, config, modalRef);

    // Handle backdrop click
    if (config.backdropDismiss !== false) {
      overlayRef.backdropClick().subscribe(() => {
        modalRef.dismiss(undefined, 'backdrop');
      });
    }

    // Handle escape key
    if (config.keyboardClose !== false) {
      overlayRef.keydownEvents().subscribe((event) => {
        if (event.key === 'Escape') {
          modalRef.dismiss(undefined, 'keyboard');
        }
      });
    }

    // Clean up when dismissed
    modalRef.afterClosed.subscribe(() => {
      this.activeModals.delete(modalId);
    });

    return modalRef;
  }

  /**
   * Dismiss a specific modal
   * @param id Modal ID
   * @param data Data to return
   * @param role Role for dismissal
   */
  async dismiss(id?: string, data?: unknown, role?: string): Promise<boolean> {
    if (id) {
      const modal = this.activeModals.get(id);
      return modal ? modal.dismiss(data, role) : false;
    }

    // Dismiss top modal if no ID provided
    const modals = Array.from(this.activeModals.values());
    const topModal = modals[modals.length - 1];
    return topModal ? topModal.dismiss(data, role) : false;
  }

  /**
   * Dismiss all open modals
   */
  async dismissAll(): Promise<void> {
    const dismissPromises = Array.from(this.activeModals.values()).map(
      (modal) => modal.dismiss(undefined, 'dismissAll')
    );
    await Promise.all(dismissPromises);
  }

  /**
   * Get an active modal by ID
   */
  getModal(id: string): ModalRef | undefined {
    return this.activeModals.get(id);
  }

  /**
   * Check if a modal is open
   */
  isModalOpen(id?: string): boolean {
    if (id) {
      return this.activeModals.has(id);
    }
    return this.activeModals.size > 0;
  }

  private createOverlay<C extends Type<unknown>>(
    config: ModalConfig<C>
  ): OverlayRef {
    const overlayConfig: OverlayConfig = {
      hasBackdrop: config.showBackdrop !== false,
      backdropClass: [
        'modal-backdrop',
        ...(config.animated !== false ? ['backdrop-animated'] : []),
      ],
      panelClass: [
        'modal-panel',
        ...(config.animated !== false ? ['modal-animated'] : []),
      ],
      scrollStrategy: this.overlay.scrollStrategies.block(),
      positionStrategy: this.overlay
        .position()
        .global()
        .centerHorizontally()
        .centerVertically(),
    };

    return this.overlay.create(overlayConfig);
  }

  private attachComponent<C extends Type<unknown>>(
    overlayRef: OverlayRef,
    config: ModalConfig<C>,
    modalRef: ModalRef<unknown>
  ): ComponentRef<InstanceType<C>> {
    // Create a custom injector that provides the modal ref
    const injector = Injector.create({
      parent: this.injector,
      providers: [{ provide: MODAL_REF, useValue: modalRef }],
    });

    // Create a component portal without a view container ref to avoid extra wrapper
    const portal = new ComponentPortal(config.component, null, injector);

    // Attach the portal directly to the overlay
    const componentRef = overlayRef.attach(portal);

    // Apply inputs after component is created
    if (config.inputs) {
      Object.entries(config.inputs).forEach(([key, value]) => {
        componentRef.setInput(key, value);
      });
    }

    // Add any custom classes to the component's host element
    if (config.cssClass) {
      const classes = Array.isArray(config.cssClass)
        ? config.cssClass
        : [config.cssClass];
      const hostElement = componentRef.location.nativeElement;
      classes.forEach((cls) => hostElement.classList.add(cls));
    }

    // Ensure change detection runs
    componentRef.changeDetectorRef.detectChanges();

    return componentRef as ComponentRef<InstanceType<C>>;
  }
}
