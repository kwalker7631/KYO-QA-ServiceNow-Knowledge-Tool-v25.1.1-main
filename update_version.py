# update_version.py
import re
from pathlib import Path
import sys

# --- Configuration ---
# List of files to update with the new version number.
FILES_TO_UPDATE = [
    "run.py", # The main launcher script
    "README.md",
    "CHANGELOG.md",
]

def get_current_version():
    """Reads the version from the single source of truth: version.py"""
    try:
        version_file = Path("version.py").read_text()
        match = re.search(r"VERSION\s*=\s*['\"]([^'\"]+)['\"]", version_file)
        if not match:
            raise RuntimeError("Could not find VERSION variable in version.py")
        return match.group(1)
    except FileNotFoundError:
        raise RuntimeError("version.py not found. Cannot determine current version.")

def update_files(new_version):
    """Updates the version number in the specified list of files."""
    print(f"Updating files to version: v{new_version}\n")
    
    # This pattern will find strings like 'v30.0.0' to update them.
    version_pattern = re.compile(r'v\d+\.\d+\.\d+')
    new_version_string = f'v{new_version}'

    for filename in FILES_TO_UPDATE:
        file_path = Path(filename)
        if not file_path.exists():
            print(f"⚠️  Skipping: {filename} (not found)")
            continue
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            new_content, num_replacements = version_pattern.subn(new_version_string, content)

            if num_replacements > 0:
                file_path.write_text(new_content, encoding='utf-8')
                print(f"✅ Updated {num_replacements} instance(s) in {filename}")
            else:
                print(f"ℹ️  No version string found to update in {filename}")
        except Exception as e:
            print(f"❌ Error updating {filename}: {e}")

if __name__ == "__main__":
    try:
        current_version = get_current_version()
        print(f"Current version from version.py: {current_version}")
        print("-" * 30)
        update_files(current_version)
        print("-" * 30)
        print("\nVersioning update process complete!")
    except Exception as e:
        print(f"\nAn error occurred: {e}", file=sys.stderr)
        sys.exit(1)
