import { Tag } from '../library/tags/tag.model';

// DTO interfaces for API responses
export interface SummaryDto {
  id: string;
  document_id: string;
  content?: string;
  summary?: string;
  word_count: number;
  processing_time: number;
  created_at?: string;
  tags?: TagDto[];
  // Additional fields from backend SummaryResponse
  document_info?: {
    id: string;
    filename: string;
    file_size: number;
    word_count?: number;
    page_count?: number;
    created_at: string;
  };
  llm_provider?: string;
  llm_model?: string;
}

export interface TagDto {
  id: string;
  name: string;
  slug: string;
  color?: string;
  document_count?: number;
}

/**
 * Domain model for Summary entity
 */
export class Summary {
  constructor(
    public readonly id: string,
    public readonly documentId: string,
    public readonly content: string,
    public readonly wordCount: number,
    public readonly processingTime: number,
    public readonly createdAt: Date,
    public readonly tags: Tag[] = []
  ) {}

  /**
   * Check if summary is brief (under 500 words)
   */
  get isBrief(): boolean {
    return this.wordCount < 500;
  }

  /**
   * Check if processing was fast (under 5 seconds)
   */
  get wasProcessedQuickly(): boolean {
    return this.processingTime < 5;
  }

  /**
   * Get a truncated preview of the summary
   */
  getPreview(maxLength = 200): string {
    if (this.content.length <= maxLength) {
      return this.content;
    }
    return this.content.substring(0, maxLength).trim() + '...';
  }

  /**
   * Format creation date
   */
  get formattedDate(): string {
    const now = new Date();
    const diffTime = now.getTime() - this.createdAt.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;

    return this.createdAt.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year:
        this.createdAt.getFullYear() !== now.getFullYear()
          ? 'numeric'
          : undefined,
    });
  }

  /**
   * Create from API response
   */
  static fromDto(dto: SummaryDto): Summary {
    // Get created_at from document_info if available, otherwise use current date
    const createdAt = dto.document_info?.created_at 
      ? new Date(dto.document_info.created_at)
      : new Date();
      
    return new Summary(
      dto.id,
      dto.document_id,
      dto.content || dto.summary || '',
      dto.word_count,
      dto.processing_time,
      createdAt,
      dto.tags?.map((t) => Tag.fromDto(t)) || []
    );
  }
}


/**
 * Value object for summary options
 */
export class SummaryOptions {
  constructor(
    public readonly style: SummaryStyle = SummaryStyle.BALANCED,
    public readonly maxLength?: number,
    public readonly focusAreas?: string,
    public readonly customPrompt?: string
  ) {}

  /**
   * Convert to API request format
   */
  toRequestParams(): Record<string, string | number> {
    const params: Record<string, string | number> = {
      style: this.style.toLowerCase(),
    };

    if (this.maxLength) {
      params['max_length'] = this.maxLength;
    }

    if (this.focusAreas) {
      params['focus_areas'] = this.focusAreas;
    }

    if (this.customPrompt) {
      params['custom_prompt'] = this.customPrompt;
    }

    return params;
  }
}

export enum SummaryStyle {
  DETAILED = 'DETAILED',
  CONCISE = 'CONCISE',
  BALANCED = 'BALANCED',
  BULLET_POINTS = 'BULLET_POINTS',
}
