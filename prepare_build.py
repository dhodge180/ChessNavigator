# This script copies the important files to a folder called
# my-build-prep
# from here a minimal working exe can be created

import shutil
import os

# Files to include
files = [
    "build.py",
    "ChessNavigator.py",
    "LICENSES.txt",
    "README.md",
    "Sample_PROBLEM_LIST.txt",
    "config.json",
    "custom_pieces.yml",
    "fairy_piece_blocks.json",
    "PROBLEM_LIST.txt"
]

# Folders to include (copy recursively)
folders = [
    "djhchess",
    "images"
]

BUILD_DIR = "my-build-prep"

# 1. Clean old build dir
shutil.rmtree(BUILD_DIR, ignore_errors=True)
os.makedirs(BUILD_DIR, exist_ok=True)

# 2. Copy files
for file in files:
    dest = os.path.join(BUILD_DIR, file)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(file, dest)
    print(f"Copied file: {file}")

# 3. Copy folders
for folder in folders:
    dest = os.path.join(BUILD_DIR, folder)
    shutil.copytree(folder, dest)
    print(f"Copied folder: {folder}")

print("\n✅ Build directory prepared in 'my-build-prep/'")
