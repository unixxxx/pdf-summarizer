import { TagDto } from '../../summary/summary.model';

/**
 * Tag model with additional properties for UI
 */
export class Tag {
  constructor(
    public readonly id: string,
    public readonly name: string,
    public readonly slug: string,
    public readonly color: string,
    public readonly documentCount?: number
  ) {}

  /**
   * Create from API response
   */
  static fromDto(dto: TagDto): Tag {
    return new Tag(
      dto.id,
      dto.name,
      dto.slug,
      dto.color || '#3B82F6', // Default blue color
      dto.document_count
    );
  }
}