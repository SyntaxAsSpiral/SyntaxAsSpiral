#!/usr/bin/env python3
"""
Test script for pulse generator - runs the live process without pushing to git.
"""

import os
import sys
from pathlib import Path
import tempfile
import shutil

def test_pulse_generation():
    """Test pulse generation by running the actual script with a temp output directory."""
    script_path = Path(__file__).resolve().parent / "github_status_rotator.py"
    
    # Create temp directory for output
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Copy assets directory to temp (needed for theme.css generation)
        assets_src = script_path.parent.parent / "assets"
        assets_dst = tmp_path / "assets"
        if assets_src.exists():
            shutil.copytree(assets_src, assets_dst)
        
        # Set environment to use temp output directory
        env = os.environ.copy()
        env["OUTPUT_DIR"] = str(tmp_path)
        env["SKIP_GIT_PUSH"] = "1"  # Flag to skip git operations
        
        print(f"🧪 Testing pulse generation...")
        print(f"📁 Output directory: {tmp_path}")
        
        # Run the actual script
        import subprocess
        result = subprocess.run(
            [sys.executable, str(script_path)],
            env=env,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.stdout:
            print("\n" + result.stdout)
        if result.stderr:
            print("Errors:", result.stderr, file=sys.stderr)
        
        # Check if index.html was created
        index_path = tmp_path / "index.html"
        if index_path.exists():
            print(f"\n✅ Test passed! Generated index.html")
            
            # Show a preview
            html = index_path.read_text(encoding="utf-8")
            if "ChronoSig" in html:
                print("✓ Contains ChronoSig")
            if "Status" in html:
                print("✓ Contains Status section")
            if "Open Portals" in html:
                print("✓ Contains Open Portals section")
            
            return 0
        else:
            print(f"\n✗ Test failed! No index.html generated")
            return 1

if __name__ == "__main__":
    sys.exit(test_pulse_generation())
