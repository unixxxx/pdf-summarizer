#!/usr/bin/env python3
"""Script to modernize type annotations from Optional[X] to X | None."""

import re
from pathlib import Path


def update_optional_syntax(file_path: Path) -> bool:
    """Update Optional[X] to X | None syntax in a file."""
    try:
        content = file_path.read_text()
        original_content = content
        
        # Pattern to match Optional[...] including nested types
        # This handles cases like Optional[dict[str, Any]]
        pattern = r'Optional\[([^\[\]]+(?:\[[^\[\]]*\])*)\]'
        
        # Replace Optional[X] with X | None
        content = re.sub(pattern, r'\1 | None', content)
        
        # Remove Optional from imports if it's no longer used
        if 'Optional[' not in content and 'from typing import' in content:
            # Handle multiline imports
            import_pattern = r'from typing import ([^)]+)'
            match = re.search(import_pattern, content, re.MULTILINE | re.DOTALL)
            if match:
                imports = match.group(1)
                # Split imports and remove Optional
                import_list = [imp.strip() for imp in imports.split(',')]
                import_list = [imp for imp in import_list if imp != 'Optional']
                
                if import_list:
                    new_imports = ', '.join(import_list)
                    content = re.sub(
                        r'from typing import [^)]+',
                        f'from typing import {new_imports}',
                        content,
                        count=1
                    )
        
        # Handle cases where Optional is the only import from typing
        content = re.sub(r'from typing import Optional\n', '', content)
        
        if content != original_content:
            file_path.write_text(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to process all Python files."""
    src_dir = Path('./src')
    
    if not src_dir.exists():
        print("Error: src directory not found!")
        return
    
    updated_files = []
    
    # Find all Python files
    for py_file in src_dir.rglob('*.py'):
        if update_optional_syntax(py_file):
            updated_files.append(py_file)
            print(f"Updated: {py_file}")
    
    print(f"\nTotal files updated: {len(updated_files)}")


if __name__ == '__main__':
    main()