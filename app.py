#!/usr/bin/env python3
"""
Recover Word files from a virus-affected flash drive.
Scans recursively (including hidden/system files) and copies .doc/.docx etc.
"""

import os
import sys
import shutil
import ctypes
from ctypes import wintypes

# Windows API constants and functions for hidden/system file detection
FILE_ATTRIBUTE_HIDDEN = 0x2
FILE_ATTRIBUTE_SYSTEM = 0x4

def get_file_attributes(path):
    """Return Windows file attributes for a given path using GetFileAttributesW."""
    attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
    if attrs == 0xFFFFFFFF:  # INVALID_FILE_ATTRIBUTES
        return 0
    return attrs

def is_hidden_or_system(path):
    """Check if file/directory has Hidden or System attribute."""
    attrs = get_file_attributes(path)
    return bool(attrs & (FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM))

def recover_word_files(src_root, dst_root, extensions=None):
    """
    Recursively copy all Word files from src_root to dst_root.
    Preserves directory structure.
    Returns list of copied files.
    """
    if extensions is None:
        extensions = {'.doc', '.docx', '.dot', '.dotx'}

    copied = []
    errors = []

    # Walk using os.scandir to detect hidden/system directories
    def scan_dir(current_src, current_dst):
        try:
            with os.scandir(current_src) as it:
                for entry in it:
                    src_path = entry.path
                    rel_path = os.path.relpath(src_path, src_root)
                    dst_path = os.path.join(dst_root, rel_path)

                    if entry.is_dir(follow_symlinks=False):
                        # Skip hidden/system directories
                        if is_hidden_or_system(src_path):
                            continue
                        # Create destination directory
                        os.makedirs(dst_path, exist_ok=True)
                        scan_dir(src_path, dst_path)
                    elif entry.is_file(follow_symlinks=False):
                        # Check if extension matches
                        if any(entry.name.lower().endswith(ext) for ext in extensions):
                            # Skip hidden/system files (optional, we can copy them)
                            # Uncomment next line if you want to skip them:
                            # if is_hidden_or_system(src_path): continue
                            try:
                                shutil.copy2(src_path, dst_path)
                                copied.append(src_path)
                                print(f"Copied: {src_path} -> {dst_path}")
                            except Exception as e:
                                errors.append((src_path, str(e)))
        except PermissionError:
            pass  # Skip inaccessible directories
        except Exception as e:
            errors.append((current_src, str(e)))

    if not os.path.exists(dst_root):
        os.makedirs(dst_root)

    scan_dir(src_root, dst_root)
    return copied, errors

def main():
    if len(sys.argv) != 3:
        print("Usage: python app.py <source_flash_drive> <destination_folder>")
        print("Example: python app.py D:\\ C:\\RecoveredDocs")
        sys.exit(1)

    src = sys.argv[1].rstrip('\\')
    dst = sys.argv[2].rstrip('\\')

    if not os.path.exists(src):
        print(f"Error: Source '{src}' does not exist.")
        sys.exit(1)

    print(f"Scanning {src} for Word files...")
    copied, errors = recover_word_files(src, dst)

    print("\n" + "="*60)
    print(f"Recovery finished. Copied {len(copied)} files.")
    if errors:
        print(f"Encountered {len(errors)} errors:")
        for path, err in errors[:10]:  # show first 10
            print(f"  {path} : {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors)-10} more.")

if __name__ == "__main__":
    main()
