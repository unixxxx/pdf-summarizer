import { Summary } from '../summary/summary.model';

export interface Tag {
  id: string;
  name: string;
  slug: string;
  color?: string;
  documentCount?: number;
}

export interface LibraryItem {
  id: string;
  documentId: string;
  filename: string;
  fileSize: number;
  summary: Summary;
  createdAt: Date;
}