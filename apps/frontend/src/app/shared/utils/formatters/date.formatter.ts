/**
 * Utility functions for date formatting
 */

/**
 * Format date as relative time (Today, Yesterday, X days ago)
 */
export function formatRelativeDate(date: Date | string): string {
  const inputDate = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();

  // Reset time parts for accurate day comparison
  const dateStart = new Date(
    inputDate.getFullYear(),
    inputDate.getMonth(),
    inputDate.getDate()
  );
  const nowStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  const diffTime = nowStart.getTime() - dateStart.getTime();
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;

  return inputDate.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: inputDate.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
  });
}

/**
 * Format date for display
 */
export function formatDate(date: Date | string): string {
  const inputDate = typeof date === 'string' ? new Date(date) : date;
  return inputDate.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

/**
 * Format date and time
 */
export function formatDateTime(date: Date | string): string {
  const inputDate = typeof date === 'string' ? new Date(date) : date;
  return inputDate.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
