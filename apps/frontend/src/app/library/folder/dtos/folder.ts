import { ChipItem } from '../../../shared/components/chip-input';
import { TagDto } from '../../tag/dtos/tag';

export interface FolderDto {
  folders: FolderItemDto[];
  total_count: number;
  unfiled_count: number;
  total_document_count: number;
}

export interface FolderItemDto {
  id: string;
  name: string;
  description: string | undefined;
  color: string;
  parent_id: string | undefined;
  tags: TagDto[];
  created_at: string;
  updated_at: string;
  document_count: number;
  children_count: number;
  children: FolderItemDto[] | undefined;
}

export interface FolderCreateDto {
  name: string;
  description: string | undefined;
  color: string;
  parent_id: string | undefined;
  tags: ChipItem[];
}

export interface FolderUpdateDto {
  name: string;
  description: string | undefined;
  color: string;
  parent_id: string | undefined;
  tags: ChipItem[];
}
