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
    icon_path = "icon2.ico"
else:
    add_data_option = "--add-data=images:images"  # Linux/macOS uses `:`
    exe_extension = ""  # No extension needed for Linux/macOS
    icon_path = "icon.png"

def build_executable():
    cmd = [
        "pyinstaller",
        "--onefile",
        "--noconsole",  # Hide terminal (for GUI apps)
        "--clean",
        f"--name={EXE_NAME}",
        f"--icon={icon_path}",
        add_data_option,
        SCRIPT_NAME
    ]

    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    build_executable()

    # Display final message
    output_file = os.path.join("dist", EXE_NAME + exe_extension)
    print(f"\n✅ Build complete! Your executable is located at: {output_file}")
