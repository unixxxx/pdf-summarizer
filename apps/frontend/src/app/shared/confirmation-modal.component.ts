import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-confirmation-modal',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (isOpen) {
      <div class="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
        <div class="flex items-center justify-center min-h-screen p-4 text-center sm:p-0">
          <div class="fixed inset-0 bg-background/80 backdrop-blur-sm transition-opacity animate-fade-in"
               (click)="onCancel()"
               (keydown.escape)="onCancel()"
               tabindex="0"
               role="button"
               aria-label="Close modal"></div>
          
          <div class="relative inline-block align-bottom glass rounded-2xl text-left overflow-hidden shadow-2xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full animate-scale-in">
            <div class="p-6 sm:p-8">
              <div class="flex items-start gap-4">
                <div class="flex-shrink-0">
                  <div class="w-12 h-12 rounded-full bg-error/10 flex items-center justify-center">
                    <svg class="w-6 h-6 text-error" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                </div>
                <div class="flex-1">
                  <h3 class="text-lg font-semibold text-foreground mb-2" id="modal-title">
                    {{ title }}
                  </h3>
                  <p class="text-muted-foreground">
                    {{ message }}
                  </p>
                </div>
              </div>
              
              <div class="mt-6 flex flex-col-reverse sm:flex-row sm:justify-end gap-3">
                <button (click)="onCancel()"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-xl font-medium text-foreground bg-muted/50 hover:bg-muted transition-all">
                  {{ cancelText }}
                </button>
                <button (click)="onConfirm()"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-xl font-medium text-white bg-error hover:bg-error/90 shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all">
                  {{ confirmText }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    }
  `,
  styles: []
})
export class ConfirmationModalComponent {
  @Input() isOpen = false;
  @Input() title = 'Confirm Action';
  @Input() message = 'Are you sure you want to proceed?';
  @Input() confirmText = 'Confirm';
  @Input() cancelText = 'Cancel';
  
  @Output() confirmed = new EventEmitter<void>();
  @Output() cancelled = new EventEmitter<void>();
  
  onConfirm() {
    this.confirmed.emit();
  }
  
  onCancel() {
    this.cancelled.emit();
  }
}