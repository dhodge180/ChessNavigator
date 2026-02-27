import subprocess
import sys
import os

EXE_NAME = "ChessNavigator"  # Name of the executable
SCRIPT_NAME = "ChessNavigator.py"  # Your main Python script

# Detect platform
is_windows = sys.platform.startswith("win")

# Correct `--add-data` path formatting for each OS
if is_windows:
    add_data_option = "--add-data=images;images"  # Windows uses `;`
    exe_extension = ".exe"  # Windows executable extension
    icon_path = "images/icon.ico"
    output_dir = os.path.join("dist_windows")
    version_file = "version_info.txt"
else:
    add_data_option = "--add-data=images:images"  # Linux/macOS uses `:`
    exe_extension = ""  # No extension needed for Linux/macOS
    icon_path = "images/icon.png"
    output_dir = os.path.join("dist_linux")
    version_file = None

def build_executable():
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconsole",  # Hide terminal (for GUI apps)
        "--noupx",
        f"--name={EXE_NAME}",
        f"--icon={icon_path}",
        f"--distpath={output_dir}",
        add_data_option,
        SCRIPT_NAME
    ]
    
    # Only include version file on Windows (Linux doesnt use it)
    if version_file:
        cmd.insert(-1, f"--version-file={version_file}")

    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    build_executable()

    # Display final message
    output_file = os.path.join(output_dir, EXE_NAME + exe_extension)
    print(f"\n✅ Build complete! Your executable is located at: {output_file}")
