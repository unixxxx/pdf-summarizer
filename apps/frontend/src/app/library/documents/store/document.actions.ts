import { createActionGroup, props } from '@ngrx/store';
import { DocumentListItem } from './state/document';
import { DocumentSearchCriteria } from '../dtos/document-search-criteria';
import { ExportFormat } from '../dtos/export-format';

export const DocumentActions = createActionGroup({
  source: 'Document',
  events: {
    // Load documents
    'Fetch Documents Command': props<{ criteria?: DocumentSearchCriteria }>(),
    'Fetch Documents Success Event': props<{
      documents: DocumentListItem[];
      total: number;
      hasMore: boolean;
      offset: number;
    }>(),
    'Fetch Documents Failure Event': props<{ error: string }>(),

    // Load more documents (pagination)
    'Fetch More Documents Command': props<{
      criteria?: DocumentSearchCriteria;
    }>(),
    'Fetch More Documents Success Event': props<{
      documents: DocumentListItem[];
      total: number;
      hasMore: boolean;
      offset: number;
    }>(),
    'Fetch More Documents Failure Event': props<{ error: string }>(),

    // Delete document
    'Delete Document Command': props<{ documentId: string }>(),
    'Delete Document Success Event': props<{
      documentId: string;
      folderId?: string;
    }>(),
    'Delete Document Failure Event': props<{ error: string }>(),

    // Export
    'Export Document Command': props<{
      documentId: string;
      format: ExportFormat;
      filename: string;
    }>(),
    'Export Document Success Event': props<{
      documentId: string;
      format: ExportFormat;
    }>(),
    'Export Document Failure Event': props<{ error: string }>(),

    // Download
    'Download Document Command': props<{
      documentId: string;
      filename: string;
    }>(),
    'Download Document Success Event': props<{ documentId: string }>(),
    'Download Document Failure Event': props<{ error: string }>(),

    // Delete modal
    'Open Delete Document Modal Command': props<{
      document: DocumentListItem;
    }>(),
  },
});
