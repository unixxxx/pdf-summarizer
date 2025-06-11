import { inject, computed } from '@angular/core';
import { interval, of } from 'rxjs';
import { takeWhile, tap, switchMap } from 'rxjs/operators';
import { tapResponse } from '@ngrx/operators';
import {
  patchState,
  signalStore,
  withComputed,
  withMethods,
  withState,
} from '@ngrx/signals';
import { rxMethod } from '@ngrx/signals/rxjs-interop';
import { SummaryService } from './summary.service';
import { Summary, SummaryOptions, SummaryStyle } from './summary.model';
import { DocumentMetadata } from '../library/documents/document.model';
import { UIStore } from '../shared/ui.store';

export interface SummaryState {
  // Input state
  inputMode: 'text' | 'file';
  inputText: string;
  selectedFile: File | null;

  // Options state
  selectedStyle: SummaryStyle;
  maxLength: number | null;
  focusAreas: string;
  customPrompt: string;

  // Processing state
  isProcessing: boolean;
  processingStatus: string;
  progress: number;

  // Result state
  summary: Summary | null;
  error: string | null;

  // UI state
  showError: boolean;
  copied: boolean;
  isDragging: boolean;
}

const initialState: SummaryState = {
  inputMode: 'text',
  inputText: '',
  selectedFile: null,
  selectedStyle: SummaryStyle.BALANCED,
  maxLength: null,
  focusAreas: '',
  customPrompt: '',
  isProcessing: false,
  processingStatus: 'Generating summary...',
  progress: 0,
  summary: null,
  error: null,
  showError: false,
  copied: false,
  isDragging: false,
};

export const SummaryStore = signalStore(
  { providedIn: 'root' },
  withState(initialState),
  withComputed((store) => ({
    wordCount: computed(() => {
      const text = store.inputText().trim();
      return text ? text.split(/\s+/).length : 0;
    }),

    canSummarize: computed(() => {
      if (store.isProcessing()) return false;

      if (store.inputMode() === 'text') {
        const text = store.inputText().trim();
        const wordCount = text ? text.split(/\s+/).length : 0;
        return wordCount >= 50;
      } else {
        return store.selectedFile() !== null;
      }
    }),

    compressionRatio: computed(() => {
      const summary = store.summary();
      if (!summary || store.inputMode() !== 'text') return 0;

      const text = store.inputText().trim();
      const originalWords = text ? text.split(/\s+/).length : 0;
      const summaryWords = summary.wordCount;

      if (originalWords === 0) return 0;
      return Math.round(((originalWords - summaryWords) / originalWords) * 100);
    }),
  })),

  withMethods((store) => {
    const summaryService = inject(SummaryService);
    const uiStore = inject(UIStore);

    // Helper functions
    const generateFilename = (text: string): string => {
      const words = text.trim().split(/\s+/);
      const meaningfulWords: string[] = [];
      const stopWords = new Set([
        'the',
        'a',
        'an',
        'and',
        'or',
        'but',
        'in',
        'on',
        'at',
        'to',
        'for',
        'of',
        'with',
        'by',
        'from',
        'as',
        'is',
        'was',
        'are',
        'were',
      ]);

      for (const word of words) {
        const cleanWord = word.toLowerCase().replace(/[^a-z0-9]/g, '');
        if (cleanWord && !stopWords.has(cleanWord) && cleanWord.length > 2) {
          meaningfulWords.push(cleanWord);
        }
        if (meaningfulWords.length >= 3) break;
      }

      if (meaningfulWords.length === 0) {
        return `summary_${Date.now()}.txt`;
      }

      const timestamp = new Date().toISOString().split('T')[0];
      return `${meaningfulWords.join('_')}_${timestamp}.txt`;
    };

    return {
      // Actions
      setInputMode(mode: 'text' | 'file'): void {
        patchState(store, { inputMode: mode });
      },

      setInputText(text: string): void {
        patchState(store, { inputText: text });
      },

      setFile(file: File | null): void {
        if (file) {
          const metadata = new DocumentMetadata(
            file.name,
            file.size,
            file.type
          );
          if (!metadata.isValid) {
            patchState(store, {
              error: metadata.validationErrors.join('. '),
              showError: true,
            });
            return;
          }
        }
        patchState(store, { selectedFile: file, error: null });
      },

      setSelectedStyle(style: SummaryStyle): void {
        patchState(store, { selectedStyle: style });
      },

      setMaxLength(length: number | null): void {
        patchState(store, { maxLength: length });
      },

      setFocusAreas(areas: string): void {
        patchState(store, { focusAreas: areas });
      },

      setCustomPrompt(prompt: string): void {
        patchState(store, { customPrompt: prompt });
      },

      setDragging(isDragging: boolean): void {
        patchState(store, { isDragging });
      },

      summarizeText: rxMethod<void>(
        switchMap(() => {
          if (!store.canSummarize()) {
            patchState(store, { showError: true });
            return of(null);
          }

          patchState(store, {
            isProcessing: true,
            error: null,
            showError: false,
            processingStatus: 'Processing text...',
            progress: 0,
          });

          // Create summary options
          const options = new SummaryOptions(
            store.selectedStyle(),
            store.maxLength() || undefined,
            store.focusAreas() || undefined,
            store.customPrompt() || undefined
          );

          const filename = generateFilename(store.inputText());

          // Progress tracking
          const progress$ = interval(300).pipe(
            takeWhile(() => store.progress() < 90),
            tap(() => {
              const currentProgress = store.progress();
              patchState(store, { progress: currentProgress + 15 });

              if (currentProgress > 30) {
                patchState(store, { processingStatus: 'Analyzing content...' });
              }
              if (currentProgress > 60) {
                patchState(store, {
                  processingStatus: 'Generating summary...',
                });
              }
            })
          );

          // Subscribe to progress updates
          progress$.subscribe();

          return summaryService
            .createForText(store.inputText(), filename, options)
            .pipe(
              tapResponse({
                next: (summary) => {
                  patchState(store, {
                    progress: 100,
                    processingStatus: 'Complete!',
                    summary,
                    isProcessing: false,
                  });
                  uiStore.showSuccess('Summary generated successfully!');
                },
                error: (err: Error) => {
                  patchState(store, {
                    isProcessing: false,
                    error: err.message || 'Failed to generate summary',
                    showError: true,
                  });
                },
              })
            );
        })
      ),

      summarizeFile: rxMethod<void>(
        switchMap(() => {
          const file = store.selectedFile();
          if (!file || !store.canSummarize()) return of(null);

          patchState(store, {
            isProcessing: true,
            error: null,
            showError: false,
            processingStatus: 'Uploading file...',
            progress: 0,
          });

          // Create summary options
          const options = new SummaryOptions(
            store.selectedStyle(),
            store.maxLength() || undefined,
            store.focusAreas() || undefined,
            store.customPrompt() || undefined
          );

          // Progress tracking
          const progress$ = interval(300).pipe(
            takeWhile(() => store.progress() < 90),
            tap(() => {
              const currentProgress = store.progress();
              patchState(store, { progress: currentProgress + 10 });

              if (currentProgress > 30) {
                patchState(store, {
                  processingStatus: 'Processing document...',
                });
              }
              if (currentProgress > 60) {
                patchState(store, {
                  processingStatus: 'Generating summary...',
                });
              }
            })
          );

          // Subscribe to progress updates
          progress$.subscribe();

          return summaryService.uploadAndSummarize(file, options).pipe(
            tapResponse({
              next: (summary) => {
                patchState(store, {
                  progress: 100,
                  processingStatus: 'Complete!',
                  summary,
                  isProcessing: false,
                });
                uiStore.showSuccess('Summary generated successfully!');
              },
              error: (err: Error) => {
                patchState(store, {
                  isProcessing: false,
                  error: err.message || 'Failed to process document',
                  showError: true,
                });
              },
            })
          );
        })
      ),

      async copyToClipboard(): Promise<void> {
        const summary = store.summary();
        if (!summary) return;

        try {
          await navigator.clipboard.writeText(summary.content);
          patchState(store, { copied: true });
          setTimeout(() => patchState(store, { copied: false }), 2000);
          uiStore.showSuccess('Summary copied to clipboard!');
        } catch {
          patchState(store, { error: 'Failed to copy to clipboard' });
          uiStore.showError('Failed to copy to clipboard');
        }
      },

      reset(): void {
        patchState(store, {
          inputText: '',
          selectedFile: null,
          summary: null,
          error: null,
          isProcessing: false,
          progress: 0,
          selectedStyle: SummaryStyle.BALANCED,
          maxLength: null,
          focusAreas: '',
          customPrompt: '',
          showError: false,
          copied: false,
        });
      },

      clearError(): void {
        patchState(store, { error: null, showError: false });
      },
    };
  })
);
