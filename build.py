import subprocess
import sys
import os
import getpass

EXE_NAME = "ChessNavigator"  # Name of the executable
SCRIPT_NAME = "ChessNavigator.py"  # Your main Python script
PFX_FILE = "chessnavigator.pfx"  # Your signing certificate file
PFX_PASSWORD = None  # Leave None to be prompted securely

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

def sign_executable():
    """Digitally sign the built EXE (Windows only)."""
    if not is_windows:
        print("🖋 Skipping signing: Not on Windows.")
        return

    exe_path = os.path.join(output_dir, EXE_NAME + exe_extension)

    if not os.path.isfile(exe_path):
        print(f"⚠️ EXE not found at {exe_path}. Build may have failed.")
        return

    if not os.path.isfile(PFX_FILE):
        print(f"⚠️ PFX file not found at {PFX_FILE}. Skipping signing.")
        return

    # Prompt for password if not hardcoded
    password = PFX_PASSWORD or getpass.getpass("Enter .pfx password: ")

    print(f"🖋 Signing {exe_path} with {PFX_FILE}...")

    signtool_cmd = [
        "signtool",
        "sign",
        "/f", PFX_FILE,
        "/p", password,
        "/fd", "SHA256",
        "/tr", "http://timestamp.digicert.com",
        "/td", "SHA256",
        exe_path
    ]

    try:
        subprocess.run(signtool_cmd, check=True)
        print("✅ EXE signed successfully!")
    except subprocess.CalledProcessError:
        print("❌ Signing failed. Please check signtool path and certificate.")

if __name__ == "__main__":
    build_executable()
    sign_executable()

    # Display final message
    output_file = os.path.join(output_dir, EXE_NAME + exe_extension)
    print(f"\n✅ Build complete! Your executable is located at: {output_file}")
