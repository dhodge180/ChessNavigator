import subprocess
import sys
import os
import getpass

EXE_NAME = "ChessNavigator"
PFX_FILE = "chessnavigator.pfx"
PFX_PASSWORD = None  # Leave None to be prompted securely

is_windows = sys.platform.startswith("win")
exe_extension = ".exe" if is_windows else ""
output_dir = "dist_windows" if is_windows else "dist_linux"


def build_executable():
    cmd = [
        "pyinstaller",
        "--clean",
        f"--distpath={output_dir}",
        "ChessNavigator.spec",
    ]
    subprocess.run(cmd, check=True)


def sign_executable():
    """Digitally sign the built EXE (Windows only)."""
    if not is_windows:
        print("Skipping signing: not on Windows.")
        return

    exe_path = os.path.join(output_dir, EXE_NAME, EXE_NAME + exe_extension)

    if not os.path.isfile(exe_path):
        print(f"EXE not found at {exe_path}. Build may have failed.")
        return

    if not os.path.isfile(PFX_FILE):
        print(f"PFX file not found at {PFX_FILE}. Skipping signing.")
        return

    password = PFX_PASSWORD or getpass.getpass("Enter .pfx password: ")
    print(f"Signing {exe_path}...")

    signtool_cmd = [
        "signtool", "sign",
        "/f", PFX_FILE,
        "/p", password,
        "/fd", "SHA256",
        "/tr", "http://timestamp.digicert.com",
        "/td", "SHA256",
        exe_path,
    ]

    try:
        subprocess.run(signtool_cmd, check=True)
        print("EXE signed successfully.")
    except subprocess.CalledProcessError:
        print("Signing failed. Check signtool path and certificate.")


if __name__ == "__main__":
    build_executable()
    sign_executable()
    output_file = os.path.join(output_dir, EXE_NAME, EXE_NAME + exe_extension)
    print(f"\nBuild complete! Executable at: {output_file}")
