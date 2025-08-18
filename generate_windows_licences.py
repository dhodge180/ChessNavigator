import subprocess
import sys
from pathlib import Path

def generate_licenses(output_path="dist_windows/ChessNavigator/THIRD_PARTY_LICENSES.txt"):
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "pip-licenses",
        "--from=mixed",

        "--format=plain",
        "--with-license-file",
        "--with-urls",
        "--no-license-path",
        f"--output-file={str(output_file)}"
    ]
    
    print(f"Generating licenses file at {output_file} ...")
    try:
        subprocess.run(cmd, check=True)
        print("✅ License file generated successfully!")
    except subprocess.CalledProcessError as e:
        print("❌ Failed to generate license file:")
        print(e)
        sys.exit(1)

if __name__ == "__main__":
    generate_licenses()
