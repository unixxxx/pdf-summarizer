import { FolderItem } from '../store/state/folder-item';

export function flattenFolders(folders: FolderItem[], level = 0): FolderItem[] {
  const result: FolderItem[] = [];
  for (const folder of folders) {
    result.push({ ...folder, name: getFolderPath(folder, level) });
    if (folder.children && folder.children.length > 0) {
      result.push(...flattenFolders(folder.children, level + 1));
    }
  }
  return result;
}

function getFolderPath(folder: FolderItem, level: number): string {
  if (level === 0) {
    return folder.name;
  }
  const indent = '\u00A0\u00A0'.repeat(level); // Non-breaking spaces
  return `${indent}└─ ${folder.name}`;
}
