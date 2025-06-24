import { Component, inject, input } from '@angular/core';
import { ModalRef, MODAL_REF } from '../../../core/services/modal';

export interface ConfirmDialogData {
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  confirmButtonClass?: string;
}

@Component({
  selector: 'app-confirm-dialog',
  standalone: true,
  template: `
    <div class="modal-content">
      <div class="modal-header">
        <div class="warning-icon">
          <svg
            class="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <h2 class="text-xl font-semibold">{{ title() }}</h2>
      </div>

      <div class="modal-body">
        <p>{{ message() }}</p>
      </div>

      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" (click)="cancel()">
          {{ cancelText() || 'Cancel' }}
        </button>
        <button
          type="button"
          [class]="confirmButtonClass() || 'btn btn-danger'"
          (click)="confirm()"
        >
          {{ confirmText() || 'Confirm' }}
        </button>
      </div>
    </div>
  `,
  styles: [
    `
      /* Modal structure styles are defined globally in styles.css */

      .warning-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 3rem;
        height: 3rem;
        background-color: rgb(var(--error) / 0.1);
        border-radius: 9999px;
        flex-shrink: 0;
      }

      .warning-icon svg {
        color: rgb(var(--error));
      }

      .modal-body p {
        color: rgb(var(--muted-foreground));
        line-height: 1.5;
      }

      .btn {
        padding: 0.5rem 1rem;
        border-radius: 0.375rem;
        font-size: 0.875rem;
        font-weight: 500;
        transition: all 0.2s;
        cursor: pointer;
        border: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
      }

      .btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      .btn-secondary {
        background-color: rgb(var(--background));
        color: rgb(var(--foreground));
        border: 1px solid rgb(var(--border));
      }

      .btn-secondary:hover {
        background-color: rgb(var(--muted) / 0.5);
      }

      .btn-danger {
        background-color: rgb(var(--error));
        color: rgb(var(--error-foreground));
      }

      .btn-danger:hover:not(:disabled) {
        background-color: rgb(var(--error) / 0.9);
      }

      .btn-primary {
        background-color: rgb(var(--primary-500));
        color: white;
      }

      .btn-primary:hover:not(:disabled) {
        background-color: rgb(var(--primary-600));
      }
    `,
  ],
})
export class ConfirmDialog {
  title = input.required<string>();
  message = input.required<string>();
  confirmText = input<string>();
  cancelText = input<string>();
  confirmButtonClass = input<string>();

  private modalRef = inject<ModalRef<boolean>>(MODAL_REF);

  confirm() {
    this.modalRef.dismiss(true, 'confirm');
  }

  cancel() {
    this.modalRef.dismiss(false, 'cancel');
  }
}
