import { OverlayRef } from '@angular/cdk/overlay';
import { Subject } from 'rxjs';
import { InjectionToken } from '@angular/core';
import { ModalRef, ModalResult } from './modal.types';

export const MODAL_REF = new InjectionToken<ModalRef>('MODAL_REF');

export class ModalRefImpl<R> implements ModalRef<R> {
  private readonly _afterClosed = new Subject<ModalResult<R>>();
  private readonly _beforeClose = new Subject<ModalResult<R>>();
  private _result?: ModalResult<R>;
  private _hasBeenDismissed = false;

  constructor(public readonly id: string, private overlayRef: OverlayRef) {}

  async dismiss(data?: R, role?: string): Promise<boolean> {
    if (this._hasBeenDismissed) {
      return false;
    }

    this._hasBeenDismissed = true;
    this._result = { data, role };

    this._beforeClose.next(this._result);
    this._beforeClose.complete();

    // Add animation class before detaching
    const overlayElement = this.overlayRef.overlayElement;
    overlayElement.classList.add('cdk-overlay-pane-detaching');

    // Add animation class to backdrop if it exists
    const backdrop = this.overlayRef.backdropElement;
    if (backdrop) {
      backdrop.style.opacity = '0';
    }

    // Wait for animation to complete
    await new Promise((resolve) => setTimeout(resolve, 200));

    this.overlayRef.dispose();

    this._afterClosed.next(this._result);
    this._afterClosed.complete();

    return true;
  }

  async onDidDismiss(): Promise<ModalResult<R>> {
    return new Promise((resolve) => {
      this._afterClosed.subscribe((result) => resolve(result));
    });
  }

  async onWillDismiss(): Promise<ModalResult<R>> {
    return new Promise((resolve) => {
      this._beforeClose.subscribe((result) => resolve(result));
    });
  }

  /** Observable of the result when the modal is closed */
  get afterClosed() {
    return this._afterClosed.asObservable();
  }

  /** Observable that emits before the modal is closed */
  get beforeClose() {
    return this._beforeClose.asObservable();
  }
}
