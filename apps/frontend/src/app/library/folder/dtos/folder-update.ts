import { ChipItem } from '../../../shared/components/chip-input';

/**
 * Folder update DTO
 * Used when updating an existing folder
 */
export interface FolderUpdateDto {
  name: string;
  description: string | undefined;
  color: string;
  parent_id: string | undefined;
  tags: ChipItem[];
}
