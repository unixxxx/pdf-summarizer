import { ToCamelCase } from '../../../../core/utils/transform';
import { ArchiveStatsDto } from '../../dtos/archive-stats';

/**
 * Archive statistics type for the store
 */
export type ArchiveStats = ToCamelCase<ArchiveStatsDto>;

/**
 * Convert ArchiveStatsDto to ArchiveStats
 */
export const toArchiveStats = (stats: ArchiveStatsDto): ArchiveStats => ({
  totalDocuments: stats.total_documents,
  totalFolders: stats.total_folders,
  totalSize: stats.total_size,
  oldestItemDate: stats.oldest_item_date,
});
