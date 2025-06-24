import {
  Summary,
  SummaryDto,
  TagDto,
} from '../../shared/models/document.model';

// DTO interface for API responses
export interface DocumentDto {
  id: string;
  filename: string;
  file_size: number;
  created_at: string;
  user_id: string;
  file_hash: string;
  extracted_text?: string;
  word_count?: number;
  storage_path?: string;
  folder_ids?: string[];
}

// Document status enum matching backend
export enum DocumentStatus {
  PENDING = 'pending',
  UPLOADING = 'uploading',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

// DTO interface for library API response
export interface LibraryItemDto {
  id: string;
  document_id: string;
  filename?: string;
  fileName?: string; // Legacy support
  file_size?: number;
  fileSize?: number; // Legacy support
  summary: string;
  word_count?: number;
  wordCount?: number; // Legacy support
  created_at?: string;
  createdAt?: string; // Legacy support
  tags?: TagDto[];
  status: DocumentStatus;
}

export interface PaginatedLibraryResponse {
  items: LibraryItemDto[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

/**
 * Domain model for Document entity
 */
export class Document {
  constructor(
    public readonly id: string,
    public readonly filename: string,
    public readonly fileSize: number,
    public readonly uploadDate: Date,
    public readonly userId: string,
    public readonly fileHash: string,
    public readonly extractedText?: string,
    public readonly wordCount?: number,
    public readonly storagePath?: string,
    public readonly folderIds: string[] = []
  ) {}

  /**
   * Check if document has been processed
   */
  get isProcessed(): boolean {
    return !!this.extractedText && !!this.wordCount;
  }

  /**
   * Check if document is recent (within 24 hours)
   */
  get isRecent(): boolean {
    const dayInMs = 24 * 60 * 60 * 1000;
    return Date.now() - this.uploadDate.getTime() < dayInMs;
  }

  /**
   * Get file extension
   */
  get extension(): string {
    const parts = this.filename.split('.');
    return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : '';
  }

  /**
   * Check if document is a PDF
   */
  get isPdf(): boolean {
    return this.extension === 'pdf';
  }

  /**
   * Format file size for display
   */
  get formattedFileSize(): string {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (this.fileSize === 0) return '0 Bytes';
    const i = Math.floor(Math.log(this.fileSize) / Math.log(1024));
    return (
      Math.round((this.fileSize / Math.pow(1024, i)) * 100) / 100 +
      ' ' +
      sizes[i]
    );
  }

  /**
   * Create from API response
   */
  static fromDto(dto: DocumentDto): Document {
    return new Document(
      dto.id,
      dto.filename,
      dto.file_size,
      new Date(dto.created_at),
      dto.user_id,
      dto.file_hash,
      dto.extracted_text,
      dto.word_count,
      dto.storage_path,
      dto.folder_ids || []
    );
  }
}

/**
 * Value object for document metadata
 */
export class DocumentMetadata {
  constructor(
    public readonly filename: string,
    public readonly fileSize: number,
    public readonly mimeType: string
  ) {}

  /**
   * Validate file size (max 10MB)
   */
  get isValidSize(): boolean {
    const maxSize = 10 * 1024 * 1024; // 10MB
    return this.fileSize <= maxSize;
  }

  /**
   * Check if file type is supported
   */
  get isSupported(): boolean {
    const supportedTypes = ['application/pdf', 'text/plain'];
    return supportedTypes.includes(this.mimeType);
  }

  /**
   * Get validation errors
   */
  get validationErrors(): string[] {
    const errors: string[] = [];

    if (!this.isValidSize) {
      errors.push('File size exceeds 10MB limit');
    }

    if (!this.isSupported) {
      errors.push('File type not supported. Please upload PDF or text files.');
    }

    return errors;
  }

  /**
   * Check if metadata is valid
   */
  get isValid(): boolean {
    return this.validationErrors.length === 0;
  }
}

/**
 * Library item model for documents with summaries
 */
export class LibraryItem {
  constructor(
    public readonly id: string,
    public readonly documentId: string,
    public readonly filename: string,
    public readonly fileSize: number,
    public readonly summary: Summary,
    public readonly createdAt: Date,
    public readonly status: DocumentStatus
  ) {}

  /**
   * Create from API response
   */
  static fromDto(dto: LibraryItemDto): LibraryItem {
    const summaryDto: SummaryDto = {
      id: dto.id,
      document_id: dto.document_id,
      content: dto.summary,
      word_count: dto.word_count || dto.wordCount || 0,
      processing_time: 0, // No longer tracked from backend
      created_at: dto.created_at || dto.createdAt || new Date().toISOString(),
      tags: dto.tags,
    };

    return new LibraryItem(
      dto.id,
      dto.document_id,
      dto.filename || dto.fileName || 'Unknown',
      dto.file_size || dto.fileSize || 0,
      Summary.fromDto(summaryDto),
      new Date(dto.created_at || dto.createdAt || new Date()),
      dto.status
    );
  }
}
