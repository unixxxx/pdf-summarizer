import { ChipItem } from '../../../shared/components/chip-input';

/**
 * Folder create DTO
 * Used when creating a new folder
 */
export interface FolderCreateDto {
  name: string;
  description: string | undefined;
  color: string;
  parent_id: string | undefined;
  tags: ChipItem[];
}
