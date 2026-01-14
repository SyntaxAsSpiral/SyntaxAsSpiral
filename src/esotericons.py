#!/usr/bin/env python3
"""
Esotericons Library - Fetch and cache mystical icons from GitHub
Provides random icon selection without local file management.
"""

import json
import random
import requests
from pathlib import Path
from typing import Optional

REPO_OWNER = "SyntaxAsSpiral"
REPO_NAME = "esotericons"
ICONS_PATH = "icons"
CACHE_FILE = Path(__file__).parent.parent / "logs" / "esotericons_cache.json"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{ICONS_PATH}"


def fetch_icon_list() -> list[str]:
    """Fetch list of icon filenames from GitHub API."""
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{ICONS_PATH}"
    
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        files = response.json()
        
        # Filter for image files
        icons = [
            f["name"] for f in files 
            if f["type"] == "file" and f["name"].lower().endswith(('.png', '.svg', '.ico', '.jpg', '.jpeg'))
        ]
        
        return sorted(icons)
    except Exception as e:
        print(f"⚠️ Failed to fetch icon list from GitHub: {e}")
        return []


def load_cache() -> dict:
    """Load cached icon list."""
    try:
        if CACHE_FILE.exists():
            with CACHE_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load icon cache: {e}")
    return {"icons": []}


def save_cache(icons: list[str]) -> None:
    """Save icon list to cache."""
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with CACHE_FILE.open("w", encoding="utf-8") as f:
            json.dump({"icons": icons}, f, indent=2)
    except Exception as e:
        print(f"⚠️ Failed to save icon cache: {e}")


def get_icon_list(refresh: bool = False) -> list[str]:
    """
    Get list of available icons.
    Uses cache unless refresh=True or cache is empty.
    """
    if not refresh:
        cache = load_cache()
        if cache.get("icons"):
            return cache["icons"]
    
    # Fetch fresh list
    icons = fetch_icon_list()
    if icons:
        save_cache(icons)
    
    return icons


def get_random_icon() -> Optional[str]:
    """
    Get a random icon URL from the esotericons repo.
    Returns GitHub raw URL that can be used directly in HTML.
    """
    icons = get_icon_list()
    if not icons:
        print("⚠️ No icons available")
        return None
    
    icon_name = random.choice(icons)
    return f"{GITHUB_RAW_BASE}/{icon_name}"


def get_icon_by_name(name: str) -> Optional[str]:
    """Get specific icon URL by filename."""
    icons = get_icon_list()
    if name in icons:
        return f"{GITHUB_RAW_BASE}/{name}"
    return None


def list_icons() -> list[str]:
    """List all available icon names."""
    return get_icon_list()


if __name__ == "__main__":
    # Test the library
    print("🔮 Esotericons Library Test")
    print(f"📁 Cache location: {CACHE_FILE}")
    
    icons = get_icon_list(refresh=True)
    print(f"\n✨ Found {len(icons)} icons:")
    for icon in icons[:10]:  # Show first 10
        print(f"  • {icon}")
    if len(icons) > 10:
        print(f"  ... and {len(icons) - 10} more")
    
    print(f"\n🎲 Random icon: {get_random_icon()}")
