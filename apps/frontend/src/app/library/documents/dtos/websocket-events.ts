import { WebSocketMessage } from '../../../core/services/websocket.service';
import { DocumentListItemDto } from './document-list-item';

export type ProcessingStage = 
  | 'queued'
  | 'downloading' 
  | 'extracting'
  | 'chunking'
  | 'embedding'
  | 'storing'
  | 'completed'
  | 'failed';

export interface DocumentProcessingEvent extends WebSocketMessage {
  type: 'document_processing';
  document_id: string;
  stage: ProcessingStage;
  progress: number; // 0-1 from backend
  timestamp?: string;
  error?: string;
  message?: string;
  document?: DocumentListItemDto; // Full document data on completion
}