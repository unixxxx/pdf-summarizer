import { ToCamelCase } from '../../../../core/utils/transform';
import { TagDto } from '../../dtos/tag';

export type Tag = ToCamelCase<TagDto>;

export const toTag = (tag: TagDto): Tag => ({
  id: tag.id,
  name: tag.name,
  color: tag.color,
  slug: tag.slug,
});
