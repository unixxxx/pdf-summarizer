import { createReducer, on } from '@ngrx/store';
import { DocumentActions } from './document.actions';
import { DocumentState } from './state/document-state';
import {
  AsyncDataItemState,
  wrapAsAsyncDataItem,
} from '../../../core/utils/async-data-item';
import { FolderActions } from '../../folder/store/folder.actions';
import { UploadActions } from '../../upload/store/upload.actions';
import { DocumentListItem } from './state/document';
import { DocumentStatus } from '../dtos/document-status';

const initialDocumentState: DocumentState = {
  documents: wrapAsAsyncDataItem([], AsyncDataItemState.IDLE),
  pagination: {
    limit: 50,
    offset: 0,
    total: 0,
    hasMore: false,
  },
};

export const documentReducer = createReducer(
  initialDocumentState,

  // Load documents
  on(DocumentActions.fetchDocumentsCommand, (state) => ({
    ...state,
    documents: {
      ...state.documents,
      state: AsyncDataItemState.LOADING,
      error: '',
    },
    pagination: {
      ...state.pagination,
      offset: 0,
    },
  })),

  on(
    DocumentActions.fetchDocumentsSuccessEvent,
    (state, { documents, total, hasMore, offset }) => ({
      ...state,
      documents: {
        state: AsyncDataItemState.LOADED,
        data: documents,
        error: '',
      },
      pagination: {
        ...state.pagination,
        total,
        hasMore,
        offset,
      },
    })
  ),

  on(DocumentActions.fetchDocumentsFailureEvent, (state, { error }) => ({
    ...state,
    documents: {
      ...state.documents,
      state: AsyncDataItemState.ERROR,
      error,
    },
  })),

  // Load more documents
  on(DocumentActions.fetchMoreDocumentsCommand, (state) => ({
    ...state,
    documents: {
      ...state.documents,
      state: AsyncDataItemState.LOADING,
    },
  })),

  on(
    DocumentActions.fetchMoreDocumentsSuccessEvent,
    (state, { documents, total, hasMore, offset }) => ({
      ...state,
      documents: {
        state: AsyncDataItemState.LOADED,
        data: [...(state.documents.data || []), ...documents],
        error: '',
      },
      pagination: {
        ...state.pagination,
        total,
        hasMore,
        offset,
      },
    })
  ),

  on(DocumentActions.fetchMoreDocumentsFailureEvent, (state, { error }) => ({
    ...state,
    documents: {
      ...state.documents,
      state: AsyncDataItemState.ERROR,
      error,
    },
  })),

  // Delete document
  on(DocumentActions.deleteDocumentSuccessEvent, (state, { documentId }) => ({
    ...state,
    documents: {
      ...state.documents,
      data:
        state.documents.data?.filter((doc) => doc.documentId !== documentId) ||
        [],
    },
    pagination: {
      ...state.pagination,
      total: Math.max(0, state.pagination.total - 1),
    },
  })),

  // Handle document moved to folder
  on(
    FolderActions.addDocumentsToFolderSuccessEvent,
    (state, { from, to, documentId }) => {
      // Find the document that was moved
      const movedDocument = state.documents.data?.find(
        (doc) => doc.documentId === documentId
      );

      if (!movedDocument) {
        return state;
      }

      // If the document is being moved to a different folder, remove it from the current list
      // This works because the document list is filtered by folder when viewing a specific folder
      const shouldRemoveFromView = from !== to;

      return {
        ...state,
        documents: {
          ...state.documents,
          data: shouldRemoveFromView
            ? state.documents.data?.filter(
                (doc) => doc.documentId !== documentId
              ) || []
            : state.documents.data?.map((doc) =>
                doc.documentId === documentId ? { ...doc, folderId: to } : doc
              ) || [],
        },
        pagination: shouldRemoveFromView
          ? {
              ...state.pagination,
              total: Math.max(0, state.pagination.total - 1),
            }
          : state.pagination,
      };
    }
  ),

  // Handle successful file upload - add to document list
  on(UploadActions.uploadFileSuccessEvent, (state, { result, folderId }) => {
    // Create a new document item from the upload result
    const newDocument: DocumentListItem = {
      id: result.documentId,
      documentId: result.documentId,
      filename: result.fileName,
      fileSize: result.fileSize,
      summary: '', // Empty string instead of null
      wordCount: 0,
      createdAt: result.uploadedAt,
      tags: [],
      status: DocumentStatus.PROCESSING,
      folderId: folderId || undefined, // Convert null to undefined
    };

    return {
      ...state,
      documents: {
        ...state.documents,
        data: [newDocument, ...(state.documents.data || [])],
      },
      pagination: {
        ...state.pagination,
        total: state.pagination.total + 1,
      },
    };
  }),

  // Handle successful text document creation - add to document list
  on(
    UploadActions.createTextDocumentSuccessEvent,
    (state, { result, folderId }) => {
      // Create a new document item from the upload result
      const newDocument: DocumentListItem = {
        id: result.documentId,
        documentId: result.documentId,
        filename: result.fileName,
        fileSize: result.fileSize,
        summary: '', // Empty string instead of null
        wordCount: 0,
        createdAt: result.uploadedAt,
        tags: [],
        status: DocumentStatus.PROCESSING,
        folderId: folderId || undefined, // Convert null to undefined
      };

      return {
        ...state,
        documents: {
          ...state.documents,
          data: [newDocument, ...(state.documents.data || [])],
        },
        pagination: {
          ...state.pagination,
          total: state.pagination.total + 1,
        },
      };
    }
  ),

  // Handle document processing updates from WebSocket
  on(
    DocumentActions.documentProcessingUpdateEvent,
    (state, { documentId, stage, progress, message }) => ({
      ...state,
      documents: {
        ...state.documents,
        data: state.documents.data?.map((doc) =>
          doc.documentId === documentId
            ? {
                ...doc,
                status: DocumentStatus.PROCESSING,
                processingStage: stage,
                processingProgress: progress,
                processingMessage: message,
              }
            : doc
        ) || [],
      },
    })
  ),

  // Handle document processing complete
  on(
    DocumentActions.documentProcessingCompleteEvent,
    (state, { document }) => ({
      ...state,
      documents: {
        ...state.documents,
        data: state.documents.data?.map((doc) =>
          doc.documentId === document.documentId
            ? {
                ...document,
                processingStage: undefined,
                processingProgress: undefined,
                processingMessage: undefined,
              }
            : doc
        ) || [],
      },
    })
  ),

  // Handle document processing failed
  on(
    DocumentActions.documentProcessingFailureEvent,
    (state, { documentId, error }) => ({
      ...state,
      documents: {
        ...state.documents,
        data: state.documents.data?.map((doc) =>
          doc.documentId === documentId
            ? {
                ...doc,
                status: DocumentStatus.FAILED,
                processingStage: undefined,
                processingProgress: undefined,
                processingMessage: undefined,
                errorMessage: error,  // Store the error message separately
              }
            : doc
        ) || [],
      },
    })
  ),

  // Handle retry processing success
  on(
    DocumentActions.retryDocumentProcessingSuccessEvent,
    (state, { documentId }) => ({
      ...state,
      documents: {
        ...state.documents,
        data: state.documents.data?.map((doc) =>
          doc.documentId === documentId
            ? {
                ...doc,
                status: DocumentStatus.PROCESSING,
                processingStage: 'queued',
                processingProgress: 0,
                processingMessage: 'Retrying document processing...',
                errorMessage: undefined,  // Clear previous error
              }
            : doc
        ) || [],
      },
    })
  ),

  // Handle document moved to unfiled
  on(
    FolderActions.moveDocumentToUnfiledSuccessEvent,
    (state, { documentId, from }) => {
      // Find the document that was moved
      const movedDocument = state.documents.data?.find(
        (doc) => doc.documentId === documentId
      );

      if (!movedDocument) {
        return state;
      }

      // If we're viewing a specific folder, remove the document from the list
      // If we're viewing all documents or unfiled, just update the folderId
      const isViewingSpecificFolder = movedDocument.folderId === from;
      
      if (isViewingSpecificFolder) {
        // Remove from current folder view
        return {
          ...state,
          documents: {
            ...state.documents,
            data: state.documents.data?.filter(
              (doc) => doc.documentId !== documentId
            ) || [],
          },
          pagination: {
            ...state.pagination,
            total: Math.max(0, state.pagination.total - 1),
          },
        };
      } else {
        // Just update the folderId for "all documents" or "unfiled" view
        return {
          ...state,
          documents: {
            ...state.documents,
            data: state.documents.data?.map((doc) =>
              doc.documentId === documentId
                ? { ...doc, folderId: undefined }
                : doc
            ) || [],
          },
        };
      }
    }
  )
);
