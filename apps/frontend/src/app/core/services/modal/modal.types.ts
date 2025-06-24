import { Type } from '@angular/core';

export interface ModalConfig<T extends Type<unknown> = Type<unknown>> {
  component: T;
  inputs?: Record<string, unknown>;
  outputs?: Record<string, (event: unknown) => void>;
  cssClass?: string | string[];
  backdropDismiss?: boolean;
  animated?: boolean;
  showBackdrop?: boolean;
  keyboardClose?: boolean;
  id?: string;
}

export interface ModalResult<T = unknown> {
  data?: T;
  role?: string;
}

export interface ModalRef<R = unknown> {
  id: string;
  dismiss(data?: R, role?: string): Promise<boolean>;
  onDidDismiss(): Promise<ModalResult<R>>;
  onWillDismiss(): Promise<ModalResult<R>>;
}
