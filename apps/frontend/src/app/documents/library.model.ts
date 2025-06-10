import { Summary, Tag } from '../summary/summary.model';

// Re-export Tag for convenience
export { Tag } from '../summary/summary.model';

export interface LibraryItem {
  id: string;
  documentId: string;
  filename: string;
  fileSize: number;
  summary: Summary;
  createdAt: Date;
}