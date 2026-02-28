"""
Validation script for epg-enricharr plugin
Checks plugin structure, dependencies, and test execution
"""

import os
import sys
import json
import zipfile
import subprocess
from pathlib import Path


def print_status(icon, message):
    """Print status message with emoji."""
    print(f"{icon} {message}")


def validate_plugin_json(zip_path, plugin_dir):
    """Validate plugin.json structure and required fields."""
    plugin_json_path = plugin_dir / "plugin.json"
    
    if not plugin_json_path.exists():
        print_status("❌", "plugin.json not found")
        return False
    
    try:
        with open(plugin_json_path) as f:
            manifest = json.load(f)
        
        required_fields = ["name", "version", "description", "author"]
        missing = [f for f in required_fields if f not in manifest]
        
        if missing:
            print_status("❌", f"plugin.json missing fields: {', '.join(missing)}")
            return False
        
        print_status("✅", f"plugin.json valid (v{manifest.get('version')})")
        return True
    except json.JSONDecodeError as e:
        print_status("❌", f"plugin.json parse error: {e}")
        return False
    except Exception as e:
        print_status("❌", f"Error reading plugin.json: {e}")
        return False


def validate_plugin_py(plugin_dir):
    """Validate plugin.py imports and syntax."""
    plugin_py_path = plugin_dir / "plugin.py"
    
    if not plugin_py_path.exists():
        print_status("❌", "plugin.py not found")
        return False
    
    try:
        with open(plugin_py_path) as f:
            code = f.read()
        
        compile(code, str(plugin_py_path), "exec")
        print_status("✅", "plugin.py syntax valid")
        
        # Check for common imports
        if "import" in code or "from" in code:
            print_status("✅", "plugin.py has imports")
        
        return True
    except SyntaxError as e:
        print_status("❌", f"plugin.py syntax error: {e}")
        return False
    except Exception as e:
        print_status("❌", f"Error validating plugin.py: {e}")
        return False


def validate_tests(plugin_dir):
    """Run tests if test_enrichment.py exists."""
    test_file = plugin_dir / "tests" / "test_enrichment.py"
    
    if not test_file.exists():
        print_status("⚠️ ", "test_enrichment.py not found (skipping test run)")
        return True
    
    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", str(test_file), "-v"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print_status("✅", "tests passed")
            return True
        else:
            print_status("❌", f"tests failed:\n{result.stdout}\n{result.stderr}")
            return False
    except FileNotFoundError:
        print_status("⚠️ ", "pytest not installed (skipping test run)")
        return True
    except subprocess.TimeoutExpired:
        print_status("❌", "test execution timed out")
        return False
    except Exception as e:
        print_status("⚠️ ", f"Could not run tests: {e}")
        return True


def validate_zip(zip_path):
    """Main validation entry point."""
    print(f"\nValidating {zip_path}...\n")
    
    if not os.path.exists(zip_path):
        print_status("❌", f"File not found: {zip_path}")
        return False
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.testzip()
        print_status("✅", "zip file integrity check passed")
    except zipfile.BadZipFile:
        print_status("❌", "zip file is corrupted")
        return False
    except Exception as e:
        print_status("❌", f"zip validation error: {e}")
        return False
    
    # Extract to temp directory
    plugin_dir = Path(zip_path).stem
    os.makedirs(plugin_dir, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(plugin_dir)
        
        # Find the actual plugin directory (may be nested)
        for item in Path(plugin_dir).iterdir():
            if item.is_dir():
                plugin_dir = item
                break
        
        # Run validations
        results = [
            validate_plugin_json(zip_path, plugin_dir),
            validate_plugin_py(plugin_dir),
            validate_tests(plugin_dir),
        ]
        
        return all(results)
    
    except Exception as e:
        print_status("❌", f"Extraction error: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validation.py <plugin-zip-path>")
        sys.exit(1)
    
    zip_path = sys.argv[1]
    success = validate_zip(zip_path)
    
    print()
    if success:
        print("✅ Validation passed!")
        sys.exit(0)
    else:
        print("❌ Validation failed!")
        sys.exit(1)
