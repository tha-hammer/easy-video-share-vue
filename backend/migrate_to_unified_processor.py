#!/usr/bin/env python3
"""
Migration Script: Consolidate Video Processing Modules
This script helps migrate from multiple video processing modules to the unified video_processor module.

Usage:
    python migrate_to_unified_processor.py --check    # Check for old imports
    python migrate_to_unified_processor.py --migrate  # Update imports
    python migrate_to_unified_processor.py --cleanup  # Remove old files (after testing)
"""

import os
import re
import argparse
import shutil
from pathlib import Path
from typing import List, Dict, Tuple

# Files to be consolidated
OLD_MODULES = [
    'video_processing_utils.py',
    'video_processing_utils_robust.py', 
    'video_processing_utils_railway.py',
    'video_processing_utils_helpers.py',
    'robust_video_processor.py',
    'simplified_video_processor.py'
]

# Import patterns to replace
IMPORT_PATTERNS = [
    # Direct imports
    (r'from video_processor import (.+)', r'from video_processor import \1'),
    (r'from video_processor import (.+)', r'from video_processor import \1'),
    (r'from video_processor import (.+)', r'from video_processor import \1'),
    (r'from video_processor import (.+)', r'from video_processor import \1'),
    (r'from video_processor import (.+)', r'from video_processor import \1'),
    (r'from video_processor import (.+)', r'from video_processor import \1'),
    
    # Specific function imports
    (r'from video_processor import get_video_duration_from_s3, calculate_segments', 
     r'from video_processor import get_video_duration_from_s3, calculate_segments'),
    (r'from video_processor import calculate_segments, validate_video_file, get_video_duration_from_s3',
     r'from video_processor import calculate_segments, validate_video_file, get_video_duration_from_s3'),
    (r'from video_processor import split_video_with_precise_timing_and_dynamic_text',
     r'from video_processor import split_video_with_precise_timing_and_dynamic_text'),
]

def find_python_files(directory: str = '.') -> List[str]:
    """Find all Python files in the directory"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip common directories that shouldn't be modified
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def check_old_imports(files: List[str]) -> Dict[str, List[str]]:
    """Check for old import patterns in files"""
    old_imports = {}
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_imports = []
            for pattern, _ in IMPORT_PATTERNS:
                matches = re.findall(pattern, content)
                if matches:
                    file_imports.extend(matches)
            
            if file_imports:
                old_imports[file_path] = file_imports
                
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return old_imports

def migrate_imports(files: List[str], dry_run: bool = True) -> Dict[str, List[str]]:
    """Migrate old imports to new unified module"""
    migrated_files = {}
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            file_changes = []
            
            # Apply import pattern replacements
            for old_pattern, new_pattern in IMPORT_PATTERNS:
                if re.search(old_pattern, content):
                    old_matches = re.findall(old_pattern, content)
                    content = re.sub(old_pattern, new_pattern, content)
                    file_changes.extend(old_matches)
            
            # Check if content changed
            if content != original_content:
                migrated_files[file_path] = file_changes
                
                if not dry_run:
                    # Write updated content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"✅ Updated: {file_path}")
                else:
                    print(f"🔍 Would update: {file_path}")
                    
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    return migrated_files

def backup_old_modules():
    """Create backup of old modules"""
    backup_dir = "backup_old_video_modules"
    os.makedirs(backup_dir, exist_ok=True)
    
    for module in OLD_MODULES:
        if os.path.exists(module):
            shutil.copy2(module, os.path.join(backup_dir, module))
            print(f"📦 Backed up: {module}")
    
    print(f"📁 Old modules backed up to: {backup_dir}")

def remove_old_modules():
    """Remove old video processing modules"""
    removed_files = []
    
    for module in OLD_MODULES:
        if os.path.exists(module):
            os.remove(module)
            removed_files.append(module)
            print(f"🗑️  Removed: {module}")
    
    if removed_files:
        print(f"✅ Removed {len(removed_files)} old modules")
    else:
        print("ℹ️  No old modules found to remove")

def main():
    parser = argparse.ArgumentParser(description='Migrate to unified video processor')
    parser.add_argument('--check', action='store_true', help='Check for old imports')
    parser.add_argument('--migrate', action='store_true', help='Migrate imports')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')
    parser.add_argument('--backup', action='store_true', help='Backup old modules')
    parser.add_argument('--cleanup', action='store_true', help='Remove old modules (after testing)')
    parser.add_argument('--all', action='store_true', help='Run all migration steps')
    
    args = parser.parse_args()
    
    if not any([args.check, args.migrate, args.backup, args.cleanup, args.all]):
        parser.print_help()
        return
    
    print("🔄 Video Processing Module Migration Tool")
    print("=" * 50)
    
    # Find Python files
    python_files = find_python_files()
    print(f"📁 Found {len(python_files)} Python files to check")
    
    if args.check or args.all:
        print("\n🔍 Checking for old imports...")
        old_imports = check_old_imports(python_files)
        
        if old_imports:
            print(f"\n❌ Found {len(old_imports)} files with old imports:")
            for file_path, imports in old_imports.items():
                print(f"  📄 {file_path}")
                for imp in imports:
                    print(f"    - {imp}")
        else:
            print("✅ No old imports found!")
    
    if args.backup or args.all:
        print("\n📦 Backing up old modules...")
        backup_old_modules()
    
    if args.migrate or args.all:
        print("\n🔄 Migrating imports...")
        dry_run = args.dry_run or args.all
        migrated_files = migrate_imports(python_files, dry_run=dry_run)
        
        if migrated_files:
            print(f"\n✅ Migrated {len(migrated_files)} files:")
            for file_path, changes in migrated_files.items():
                print(f"  📄 {file_path}")
                for change in changes:
                    print(f"    - {change}")
        else:
            print("ℹ️  No files needed migration")
    
    if args.cleanup or args.all:
        print("\n🗑️  Cleaning up old modules...")
        remove_old_modules()
    
    print("\n🎉 Migration complete!")
    
    if args.all:
        print("\n📋 Next steps:")
        print("1. Test the application with the new unified video_processor module")
        print("2. Run your test suite to ensure everything works")
        print("3. If everything works, you can safely delete the backup directory")
        print("4. Update any documentation that references the old modules")

if __name__ == "__main__":
    main() 