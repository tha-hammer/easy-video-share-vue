#!/usr/bin/env python3
"""
Cleanup Test Files for Sprint 2

This script removes all development/debug test files that are no longer
needed for production use of Sprint 2.
"""

import os
import sys
from pathlib import Path

class TestFileCleanup:
    def __init__(self):
        self.backend_dir = Path(__file__).parent
        
        # List of test/debug files to remove
        self.test_files = [
            # Video processing test files
            "test_video_processing.py",
            "test_imagemagick.py", 
            "fix_moviepy_imagemagick.py",
            "diagnose_ffmpeg.py",
            "minimal_video_test.py",
            "robust_video_processor.py",
            "test_fps_fix.py",
            "manual_moviepy_config.py",
            "simplified_video_processor.py",
            
            # Integration test files
            "real_upload_test.py",
            "test_sprint_2.py", 
            "debug_processing.py",
            
            # Infrastructure test files
            "test_redis_connection.py",
            "test_aws_auth.py",
            
            # Generated test files
            "test_video.mp4",
            "test_output_segment_0.mp4",
            "test_output_segment_1.mp4", 
            "test_output_segment_2.mp4",
            
            # Other debug files
            "debug_*.py",
            "temp_*.py",
            "*_test_*.mp4",
        ]
        
        # Files to keep (production code)
        self.keep_files = [
            "main.py",
            "tasks.py", 
            "models.py",
            "config.py",
            "s3_utils.py",
            "video_processing_utils_robust.py",
            "requirements.txt",
            "README.md",
            "run_server.py",
            "run_worker.py",
            
            # Validation files (can be removed later)
            "validate_sprint2.py",
            "test_sprint2_e2e.py",
            "create_test_video.py",
            "cleanup_test_files.py"
        ]
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        symbols = {"INFO": "ℹ", "SUCCESS": "✓", "ERROR": "❌", "WARNING": "⚠"}
        symbol = symbols.get(level, "•")
        print(f"{symbol} {message}")
        
    def find_test_files(self) -> list:
        """Find all test files to remove"""
        files_to_remove = []
        
        for pattern in self.test_files:
            if "*" in pattern:
                # Handle wildcard patterns
                import glob
                matches = glob.glob(str(self.backend_dir / pattern))
                for match in matches:
                    file_path = Path(match)
                    if file_path.is_file():
                        files_to_remove.append(file_path)
            else:
                # Handle exact file names
                file_path = self.backend_dir / pattern
                if file_path.exists():
                    files_to_remove.append(file_path)
                    
        return files_to_remove
        
    def show_files_to_remove(self, files: list):
        """Show files that will be removed"""
        if not files:
            self.log("No test files found to remove", "INFO")
            return
            
        self.log(f"Found {len(files)} test files to remove:", "INFO")
        for file_path in files:
            file_size = file_path.stat().st_size if file_path.exists() else 0
            self.log(f"  {file_path.name} ({file_size:,} bytes)", "WARNING")
            
    def remove_files(self, files: list, dry_run: bool = True) -> bool:
        """Remove test files"""
        if not files:
            self.log("No files to remove", "INFO")
            return True
            
        removed_count = 0
        total_size = 0
        
        for file_path in files:
            if file_path.exists():
                file_size = file_path.stat().st_size
                
                if not dry_run:
                    try:
                        file_path.unlink()
                        self.log(f"Removed: {file_path.name}", "SUCCESS")
                        removed_count += 1
                        total_size += file_size
                    except Exception as e:
                        self.log(f"Failed to remove {file_path.name}: {e}", "ERROR")
                else:
                    self.log(f"Would remove: {file_path.name}", "INFO")
                    removed_count += 1
                    total_size += file_size
                    
        if dry_run:
            self.log(f"Dry run complete: {removed_count} files ({total_size:,} bytes)", "INFO")
        else:
            self.log(f"Cleanup complete: {removed_count} files removed ({total_size:,} bytes freed)", "SUCCESS")
            
        return True
        
    def show_production_files(self):
        """Show production files that will be kept"""
        self.log("\nProduction files (keeping):", "INFO")
        
        production_files = []
        for file_name in self.keep_files:
            file_path = self.backend_dir / file_name
            if file_path.exists():
                production_files.append(file_path)
                
        for file_path in production_files:
            file_size = file_path.stat().st_size
            self.log(f"  ✓ {file_path.name} ({file_size:,} bytes)", "SUCCESS")
            
        # Show any other Python files that might be production code
        all_py_files = list(self.backend_dir.glob("*.py"))
        other_files = [f for f in all_py_files if f not in production_files]
        
        if other_files:
            self.log("\nOther Python files found:", "WARNING")
            for file_path in other_files:
                file_size = file_path.stat().st_size
                self.log(f"  ? {file_path.name} ({file_size:,} bytes)", "WARNING")
                
    def run_cleanup(self, dry_run: bool = True) -> bool:
        """Run the cleanup process"""
        self.log("=" * 50, "INFO")
        self.log("Sprint 2 Test File Cleanup", "INFO")
        self.log("=" * 50, "INFO")
        
        # Find test files
        test_files = self.find_test_files()
        
        # Show what will be removed
        self.show_files_to_remove(test_files)
        
        # Show production files
        self.show_production_files()
        
        if not test_files:
            self.log("\nNo test files to clean up!", "SUCCESS")
            return True
            
        if dry_run:
            self.log(f"\nThis is a DRY RUN - no files will be actually removed", "WARNING")
            self.remove_files(test_files, dry_run=True)
            
            self.log("\nTo actually remove files, run:", "INFO")
            self.log("  python cleanup_test_files.py --confirm", "INFO")
        else:
            self.log(f"\nRemoving {len(test_files)} test files...", "WARNING")
            success = self.remove_files(test_files, dry_run=False)
            
            if success:
                self.log("\n🎉 Cleanup completed successfully!", "SUCCESS")
                self.log("Sprint 2 is now production-ready", "SUCCESS")
            else:
                self.log("\n❌ Cleanup had some errors", "ERROR")
                
            return success


def main():
    """Main function"""
    cleanup = TestFileCleanup()
    
    # Check if user wants to actually remove files
    confirm = "--confirm" in sys.argv or "-y" in sys.argv
    
    if not confirm:
        print("Test File Cleanup - Dry Run Mode")
        print("=" * 40)
        print("This will show what files would be removed without actually removing them.")
        print("Use --confirm to actually remove the files.\n")
        
    success = cleanup.run_cleanup(dry_run=not confirm)
    
    if success and not confirm:
        print("\n💡 To proceed with actual cleanup:")
        print("   python cleanup_test_files.py --confirm")
        
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
