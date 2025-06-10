// DTO interface for API responses
export interface DocumentDto {
  id: string;
  filename: string;
  file_size: number;
  upload_date: string;
  user_id: string;
  file_hash: string;
  extracted_text?: string;
  word_count?: number;
  storage_path?: string;
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
    public readonly storagePath?: string
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
      new Date(dto.upload_date),
      dto.user_id,
      dto.file_hash,
      dto.extracted_text,
      dto.word_count,
      dto.storage_path
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
