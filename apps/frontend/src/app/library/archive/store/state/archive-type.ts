import { ArchiveStats } from './archive-stats';
import { ArchivedFolderWithChildren } from './archived-folder-with-children';
import { ArchivedDocument } from './archived-document';

/**
 * Main archive type containing all archive data
 */
export interface Archive {
  stats: ArchiveStats;
  folders: ArchivedFolderWithChildren[];
  documents: ArchivedDocument[];
}
