/**
 * Utility functions for file size formatting
 */

/**
 * Format file size in human readable format
 */
export function formatFileSize(bytes: number): string {
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  if (bytes === 0) return '0 Bytes';

  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  const formattedSize = Math.round((bytes / Math.pow(1024, i)) * 100) / 100;

  return `${formattedSize} ${sizes[i]}`;
}

/**
 * Validate file size against limit
 */
export function isFileSizeValid(bytes: number, maxSizeMB = 10): boolean {
  const maxBytes = maxSizeMB * 1024 * 1024;
  return bytes <= maxBytes;
}

/**
 * Get file size validation message
 */
export function getFileSizeError(bytes: number, maxSizeMB = 10): string | null {
  if (isFileSizeValid(bytes, maxSizeMB)) {
    return null;
  }

  return `File size (${formatFileSize(bytes)}) exceeds ${maxSizeMB}MB limit`;
}
