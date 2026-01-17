#!/usr/bin/env python3
"""
GitHub Status Rotator - Generates dynamic pulse log homepage
Uses LLM-based pulse generator with fallback to batch cycling.
"""

import os
import time
import json
import yaml
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import random
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import pulse generator
try:
    from pulse_generator import generate_all_pulse_fields, FIELD_MAPPINGS
    PULSE_GENERATOR_AVAILABLE = True
except ImportError:
    PULSE_GENERATOR_AVAILABLE = False
    print("⚠️ Pulse generator not available, using batch cycling fallback")

# Import template renderer
from template_renderer import render_template, render, inject

# === CONFIGURATION ===
REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "config"
STYLE_CONFIG_YAML = CONFIG_DIR / "style-config.yaml"


def load_theme() -> dict:
    """Load optional theme settings from YAML."""
    try:
        with STYLE_CONFIG_YAML.open(encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            theme = data.get("theme") or {}
            return theme if isinstance(theme, dict) else {}
    except FileNotFoundError:
        return {}


def write_theme_css(output_dir: Path, theme: dict) -> None:
    """Write a small CSS variables file consumed by style.css."""
    page_background = theme.get("page_background")
    frame_shadow_color = theme.get("frame_shadow_color")
    link_color = theme.get("link_color")
    strong_color = theme.get("strong_color")

    lines = [":root {"]
    if page_background:
        lines.append(f"  --page-bg: {page_background};")
    if frame_shadow_color:
        # Convert hex to rgba and build shadow
        hex_color = frame_shadow_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        shadow = f"0 0 25px 5px rgba({r}, {g}, {b}, 0.25), inset 0 0 15px 2px rgba({r}, {g}, {b}, 0.15)"
        lines.append(f"  --frame-shadow: {shadow};")
    if link_color:
        lines.append(f"  --link-color: {link_color};")
    if strong_color:
        lines.append(f"  --strong-color: {strong_color};")
    lines.append("}")
    lines.append("")

    theme_path = output_dir / "theme.css"
    theme_path.write_text("\n".join(lines), encoding="utf-8")


def apply_zalgo_light(text: str, rng: random.Random) -> str:
    """Apply light zalgo combining marks to text for visual distortion."""
    # Load zalgo config
    config_path = REPO_ROOT / "config" / "zalgo-config.json"
    try:
        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)
        zalgo_cfg = config.get("zalgo", {})
    except:
        # Fallback to defaults if config missing
        zalgo_cfg = {
            "intensity": 4,
            "style": "rootglow",
            "allowUp": True,
            "allowMid": True,
            "allowDown": True
        }
    
    # Style-specific mark pools (from zalgo-lexigon)
    styles = {
        "rootglow": {
            "up": ["\u0306", "\u0307", "\u0308", "\u0304"],
            "mid": ["\u0334", "\u0335", "\u0336", "\u0331"],
            "down": ["\u0331", "\u0332", "\u0333", "\u0323", "\u0330", "\u032C", "\u032D", "\u032E", "\u032F", "\u035F", "\u0345", "\u0339", "\u0347", "\u0348", "\u0349"],
            "density": [0.12, 0.20, 1.35]
        },
        "classic": {
            "up": ["\u0300", "\u0301", "\u0302", "\u0303", "\u0304", "\u0306", "\u0307", "\u0308"],
            "mid": ["\u0334", "\u0335", "\u0336", "\u0337"],
            "down": ["\u0323", "\u0324", "\u0331", "\u0332"],
            "density": [0.6, 0.4, 0.7]
        }
    }
    
    style_name = zalgo_cfg.get("style", "rootglow")
    palette = styles.get(style_name, styles["rootglow"])
    intensity = zalgo_cfg.get("intensity", 4)
    allow_up = zalgo_cfg.get("allowUp", True)
    allow_mid = zalgo_cfg.get("allowMid", True)
    allow_down = zalgo_cfg.get("allowDown", True)
    
    # Calculate mark counts based on intensity and density
    mult = intensity / 100
    base_factor = 2 + 6 * mult
    up_count = int(base_factor * palette["density"][0]) if allow_up else 0
    mid_count = int(base_factor * palette["density"][1]) if allow_mid else 0
    down_count = int(base_factor * palette["density"][2]) if allow_down else 0
    
    result = []
    for char in text:
        if char.isspace():
            result.append(char)
            continue
        
        result.append(char)
        # Apply marks with jitter
        jitter = lambda: 1 if rng.random() < 0.2 else 0
        
        for _ in range(up_count + jitter()):
            result.append(rng.choice(palette["up"]))
        for _ in range(mid_count + jitter()):
            result.append(rng.choice(palette["mid"]))
        for _ in range(down_count + jitter()):
            result.append(rng.choice(palette["down"]))
    
    return ''.join(result)


def render_logs_index_html(log_dates: list[str], logs_dir: Path, icon_tag: str = "") -> str:
    """Render logs index page from template with dynamic log items."""
    import re
    
    items = []
    for d in log_dates:
        # Hardcode sufi icon for first pulse log
        if d == "2026-01-13":
            icon_url = "https://raw.githubusercontent.com/SyntaxAsSpiral/esotericons/main/icons/sufi.svg"
        else:
            # Extract icon URL from archived log
            log_path = logs_dir / f"{d}.html"
            icon_url = None
            try:
                with log_path.open("r", encoding="utf-8") as f:
                    content = f.read()
                    # Match <link rel="icon" href="..." ...>
                    match = re.search(r'<link rel="icon" href="([^"]+)"', content)
                    if match:
                        icon_url = match.group(1)
            except Exception:
                pass
        
        # Build list item with icon - logs-index.html lives at root, so links need logs/ prefix
        if icon_url:
            items.append(f'      <li><img src="{icon_url}" class="log-icon" alt=""> <a href="logs/{d}.html">{d}</a></li>')
        else:
            items.append(f'      <li><a href="logs/{d}.html">{d}</a></li>')
    
    log_items = "\n".join(items) if items else "      <li><em>No logs yet.</em></li>"
    
    # Load template from root
    template_path = Path(__file__).parent.parent / "logs-index.html"
    try:
        with template_path.open("r", encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        raise RuntimeError(f"logs-index.html template not found at {template_path}")
    
    # Render template
    return template.replace("{{icon_tag}}", icon_tag).replace("{{log_items}}", log_items)


# === FALLBACK: Batch Cycling (if LLM unavailable) ===
def lines_from_env_or_file(env_var: str, file_var: str, default_path: Path, fallback: list[str]) -> list[str]:
    """Breathe from env text or file path."""
    if env_var in os.environ:
        return [ln.strip() for ln in os.environ[env_var].splitlines() if ln.strip()]
    path = Path(os.environ.get(file_var, default_path))
    return breathe_lines(path, fallback)


def breathe_lines(path: Path, fallback: list[str]) -> list[str]:
    """Inhale lines from a path or exhale the fallback."""
    try:
        with path.open(encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return fallback


def read_cache(path: Path) -> list[str]:
    """Exhale memory traces from a cache file."""
    try:
        with path.open(encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []


def write_cache(path: Path, lines: list[str]) -> None:
    """Inscribe the latest traces back into the cache."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln + "\n")


def batch_cycle_choice(options: list[str], cache_path: Path, batch_size: int = 5) -> str:
    """Return next value from a batch cycle cache (fallback method)."""
    cycle = read_cache(cache_path)
    if not cycle:
        unique = []
        seen = set()
        for opt in options:
            if opt and opt not in seen:
                unique.append(opt)
                seen.add(opt)
        if not unique:
            return ""
        sample_size = min(batch_size, len(unique))
        cycle = random.sample(unique, sample_size)
    choice = cycle.pop(0)
    write_cache(cache_path, cycle)
    return choice


# === FALLBACK: Load seed lists for batch cycling ===
DEFAULT_STATUS = REPO_ROOT / "logs" / "pulses" / "seeds" / "statuses.txt"
STATUS_FILE = Path(os.environ.get("STATUS_FILE", DEFAULT_STATUS))
STATUS_LIST = lines_from_env_or_file("STATUSES", "STATUS_FILE", DEFAULT_STATUS, ["⚠️ status file missing"])

DEFAULT_STATUS_CACHE = REPO_ROOT / "logs" / "pulses" / "status_cache.txt"
STATUS_CACHE_FILE = Path(os.environ.get("STATUS_CACHE_FILE", DEFAULT_STATUS_CACHE))
STATUS_CACHE_LIMIT = int(os.environ.get("STATUS_CACHE_LIMIT", "5"))

DEFAULT_QUOTE = REPO_ROOT / "logs" / "pulses" / "seeds" / "antenna_quotes.txt"
QUOTE_FILE = Path(os.environ.get("QUOTE_FILE", DEFAULT_QUOTE))
QUOTE_LIST = lines_from_env_or_file("ANTENNA_QUOTES", "QUOTE_FILE", DEFAULT_QUOTE, ["⚠️ quote file missing"])

DEFAULT_QUOTE_CACHE = REPO_ROOT / "logs" / "pulses" / "quote_cache.txt"
QUOTE_CACHE_FILE = Path(os.environ.get("QUOTE_CACHE_FILE", DEFAULT_QUOTE_CACHE))
QUOTE_CACHE_LIMIT = int(os.environ.get("QUOTE_CACHE_LIMIT", "5"))

DEFAULT_GLYPH = REPO_ROOT / "logs" / "pulses" / "seeds" / "glyphbraids.txt"
GLYPH_FILE = Path(os.environ.get("GLYPH_FILE", DEFAULT_GLYPH))
GLYPH_LIST = lines_from_env_or_file("GLYPH_BRAIDS", "GLYPH_FILE", DEFAULT_GLYPH, ["⚠️ glyph file missing"])

DEFAULT_GLYPH_CACHE = REPO_ROOT / "logs" / "pulses" / "glyph_cache.txt"
GLYPH_CACHE_FILE = Path(os.environ.get("GLYPH_CACHE_FILE", DEFAULT_GLYPH_CACHE))
GLYPH_CACHE_LIMIT = int(os.environ.get("GLYPH_CACHE_LIMIT", "5"))

DEFAULT_SUBJECT = REPO_ROOT / "logs" / "pulses" / "seeds" / "subject-ids.txt"
SUBJECT_FILE = Path(os.environ.get("SUBJECT_FILE", DEFAULT_SUBJECT))
SUBJECT_LIST = lines_from_env_or_file("SUBJECT_IDS", "SUBJECT_FILE", DEFAULT_SUBJECT, ["⚠️ subject file missing"])

DEFAULT_SUBJECT_CACHE = REPO_ROOT / "logs" / "pulses" / "subject_cache.txt"
SUBJECT_CACHE_FILE = Path(os.environ.get("SUBJECT_CACHE_FILE", DEFAULT_SUBJECT_CACHE))
SUBJECT_CACHE_LIMIT = int(os.environ.get("SUBJECT_CACHE_LIMIT", "5"))

DEFAULT_ECHO = REPO_ROOT / "logs" / "pulses" / "seeds" / "echo_fragments.txt"
ECHO_FILE = Path(os.environ.get("ECHO_FILE", DEFAULT_ECHO))
ECHO_LIST = lines_from_env_or_file("ECHO_FRAGMENTS", "ECHO_FILE", DEFAULT_ECHO, ["⚠️ echo file missing"])

DEFAULT_ECHO_CACHE = REPO_ROOT / "logs" / "pulses" / "echo_cache.txt"
ECHO_CACHE_FILE = Path(os.environ.get("ECHO_CACHE_FILE", DEFAULT_ECHO_CACHE))
ECHO_CACHE_LIMIT = int(os.environ.get("ECHO_CACHE_LIMIT", "5"))

DEFAULT_MODE = REPO_ROOT / "logs" / "pulses" / "seeds" / "modes.txt"
MODE_FILE = Path(os.environ.get("MODE_FILE", DEFAULT_MODE))
raw_modes = lines_from_env_or_file("MODES", "MODE_FILE", DEFAULT_MODE, ["⚠️ mode file missing"])
MODE_LIST = []
for m in raw_modes:
    txt = m.strip().strip(',')
    if txt.startswith("mode_options") or txt in {"[", "]"}:
        continue
    if txt.startswith("\"") and txt.endswith("\""):
        txt = txt[1:-1]
    MODE_LIST.append(txt)
if not MODE_LIST:
    MODE_LIST = ["⚠️ mode file missing"]

DEFAULT_MODE_CACHE = REPO_ROOT / "logs" / "pulses" / "mode_cache.txt"
MODE_CACHE_FILE = Path(os.environ.get("MODE_CACHE_FILE", DEFAULT_MODE_CACHE))
MODE_CACHE_LIMIT = int(os.environ.get("MODE_CACHE_LIMIT", "5"))

DEFAULT_END_QUOTE = REPO_ROOT / "logs" / "pulses" / "seeds" / "end-quotes.txt"
END_QUOTE_FILE = Path(os.environ.get("END_QUOTE_FILE", DEFAULT_END_QUOTE))
END_QUOTE_LIST = lines_from_env_or_file("END_QUOTES", "END_QUOTE_FILE", DEFAULT_END_QUOTE, ["⚠️ end quote file missing"])

DEFAULT_END_QUOTE_CACHE = REPO_ROOT / "logs" / "pulses" / "end_quote_cache.txt"
END_QUOTE_CACHE_FILE = Path(os.environ.get("END_QUOTE_CACHE_FILE", DEFAULT_END_QUOTE_CACHE))
END_QUOTE_CACHE_LIMIT = int(os.environ.get("END_QUOTE_CACHE_LIMIT", "5"))


def get_pulse_value(field_name: str, fallback_list: list[str], cache_path: Path, cache_limit: int, llm_config: dict = None) -> str:
    """
    Get pulse value using LLM generation if available, otherwise batch cycling.
    """
    if PULSE_GENERATOR_AVAILABLE:
        # Try LLM generation first
        seed_file_map = {
            "status": "statuses",
            "quote": "antenna_quotes",
            "glyph": "glyphbraids",
            "subject": "subject-ids",
            "echo": "echo_fragments",
            "mode": "modes",
            "end_quote": "end-quotes",
        }
        seed_file = seed_file_map.get(field_name)
        if seed_file:
            # Use provided config or load fresh
            if llm_config:
                from pulse_generator import load_seeds, generate_with_llm
                import random
                seeds = load_seeds(seed_file)
                if seeds:
                    generated = generate_with_llm(seed_file, seeds, llm_config)
                    if generated:
                        return generated
            else:
                generated = generate_pulse_field(seed_file, fallback_to_random=False)
                if generated:
                    return generated
    
    # Fallback to batch cycling
    return batch_cycle_choice(fallback_list, cache_path, cache_limit)


def generate_field_worker(args: tuple) -> tuple[str, str]:
    """Worker function for parallel generation."""
    field_name, seed_file, fallback_list, cache_path, cache_limit, active_backend = args
    
    if PULSE_GENERATOR_AVAILABLE and active_backend:
        from pulse_generator import load_seeds, generate_with_llm
        import random
        seed_examples, cache_examples = load_seeds(seed_file)
        if seed_examples or cache_examples:
            generated = generate_with_llm(seed_file, seed_examples, cache_examples, active_backend)
            if generated:
                # Write to cache to preserve LLM outputs (no trimming)
                cache = read_cache(cache_path)
                cache.append(generated)
                write_cache(cache_path, cache)
                return (field_name, generated)
    
    # Fallback to batch cycling
    value = batch_cycle_choice(fallback_list, cache_path, cache_limit)
    return (field_name, value)


def main():
    """Generate pulse log homepage."""
    # Load LLM config once (not 7 times!)
    active_backend = None
    if PULSE_GENERATOR_AVAILABLE:
        from pulse_generator import load_llm_config, select_active_backend
        llm_config = load_llm_config()
        
        # Fast-fail: test both backends, exit if both unreachable
        print(f"🔧 Testing LLM backends...")
        active_backend = select_active_backend(llm_config)
        
        if active_backend is None:
            print(f"✗ FATAL: Both primary and fallback LLM backends unreachable")
            print(f"  Primary: {llm_config['primary']['base_url']}")
            print(f"  Fallback: {llm_config['fallback']['base_url']}")
            print("  Either start LMStudio or check OpenRouter API key in secrets.env")
            sys.exit(1)
        
        print(f"  ✓ Using {active_backend['provider']} backend")
    
    # Generate pulse fields using 3-phase hybrid architecture
    print("🌀 Generating pulse fields...")
    
    results = {}
    if active_backend and PULSE_GENERATOR_AVAILABLE:
        # Use new 3-phase batch generation
        results = generate_all_pulse_fields()
        
        if not results:
            print("  ✗ FATAL: Pulse generation failed")
            print("  Fast-fail: no fallback to batch cycling (by design)")
            sys.exit(1)
    else:
        print("  ✗ FATAL: No LLM backend available")
        sys.exit(1)
    
    status = results.get("status", "")
    quote = results.get("quote", "")
    braid = results.get("glyph", "")
    subject = results.get("subject", "")
    classification = results.get("echo", "")
    end_quote = results.get("end_quote", "")
    mode = results.get("mode", "")
    
    class_disp = f"⊚ ⇝ Echo Fragment {classification}"
    class_disp_html = class_disp.replace("Echo Fragment", "<strong>Echo Fragment</strong>")
    
    pacific = ZoneInfo("America/Los_Angeles")
    timestamp = datetime.now(pacific).strftime("%Y-%m-%d %H:%M %Z")        
    log_date = datetime.now(pacific).strftime("%Y-%m-%d")
    chronotonic = hex(time.time_ns())[-6:]

    output_dir = Path(os.environ.get("OUTPUT_DIR", REPO_ROOT))  
    output_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
    print(f"📁 Output directory: {output_dir.absolute()}")

    stylesheet = os.environ.get("STYLESHEET", "style.css")

    theme = load_theme()
    write_theme_css(output_dir / "assets", theme)

    subject_fonts = [
        "Recursive",
        "Fira Mono",
        "Cascadia Mono",
        "Consolas",
        "Courier New",
        "monospace",
    ]
    subject_font = random.Random(chronotonic).choice(subject_fonts)
    
    # Apply zalgo only to the part before ⊚
    if '⊚' in subject:
        before, after = subject.split('⊚', 1)
        subject_zalgo = apply_zalgo_light(before, random.Random(chronotonic)) + '⊚' + after
    else:
        subject_zalgo = apply_zalgo_light(subject, random.Random(chronotonic))

    # Get random esotericon (with fallback)
    try:
        from esotericons import get_random_icon
        icon_url = get_random_icon()
        if icon_url:
            # Determine icon type from URL
            if icon_url.endswith('.svg'):
                icon_tag = f'<link rel="icon" href="{icon_url}" type="image/svg+xml">'
            elif icon_url.endswith('.png'):
                icon_tag = f'<link rel="icon" href="{icon_url}" type="image/png">'
            else:
                icon_tag = f'<link rel="icon" href="{icon_url}">'
        else:
            # Fallback to local icon
            icon_tag = '<link rel="icon" href="assets/index.ico" type="image/x-icon">'
    except Exception as e:
        print(f"⚠️ Failed to get esotericon, using fallback: {e}")
        icon_tag = '<link rel="icon" href="assets/index.ico" type="image/x-icon">'

    # === BUILD PULSE DATA ===
    logs_link_html = '<p><a href="logs-index.html">See past logs :: ></a></p>'

    # Split chronohex into individual characters for rainbow coloring
    chronohex_chars = {f"chronohex_{i}": c for i, c in enumerate(chronotonic[:6])}

    pulse_data = {
        "chronotonic": chronotonic,
        "chronohex": chronotonic,  # alias for templates
        **chronohex_chars,  # chronohex_0 through chronohex_5
        "timestamp": timestamp,
        "stylesheet": stylesheet,
        "icon_tag": icon_tag,
        "quote": quote,
        "subject_font": subject_font,
        "subject_zalgo": subject_zalgo,
        "braid": braid,
        "status": status,
        "mode": mode,
        "class_disp_html": class_disp_html,
        "end_quote": end_quote,
        "logs_link_html": logs_link_html,
    }

    # Write pulse.json for UI-agnostic consumption
    pulse_json_path = output_dir / "logs" / "pulses" / "pulse.json"
    pulse_json_path.parent.mkdir(parents=True, exist_ok=True)
    with pulse_json_path.open("w", encoding="utf-8") as f:
        json.dump(pulse_data, f, indent=2, ensure_ascii=False)
    print(f"📝 pulse.json written to {pulse_json_path}")

    # === RENDER HTML FROM TEMPLATE ===
    html_content = render_template("default", pulse_data)

    html_path = output_dir / "index.html"
    with html_path.open("w", encoding="utf-8") as f:
        f.write(html_content)
        if not html_content.endswith("\n"):
            f.write("\n")

    print(f"✅ index.html updated with status: {status}")

    # === RENDER STATIC PAGES WITH PULSE DATA ===
    # Static pages use injection markers: <!--{{var}}-->...<!--/{{var}}-->
    # Markers are preserved, content between is replaced with fresh values
    static_pages = ["about.html", "projects.html", "utils.html", "zalgo-lexigon.html", "palette-mutator.html"]
    for page_name in static_pages:
        page_path = output_dir / page_name
        if page_path.exists():
            page_content = page_path.read_text(encoding="utf-8")
            rendered = inject(page_content, pulse_data)
            page_path.write_text(rendered, encoding="utf-8")
            print(f"✅ {page_name} injected with pulse data")

    # === UPDATE README.md ===
    readme_path = REPO_ROOT / "README.md"
    try:
        with readme_path.open("r", encoding="utf-8") as f:
            readme_content = f.read()
        
        # Update chronohex in README (handles both plain backticks and markdown links)
        import re
        updated_readme = re.sub(
            r'### 🌀 Current (?:Recursive )?Pulse Log ⟳ ChronoHex ⟐ (?:`[^`]+`|\[`[^`]+`\]\([^)]+\)|<a href="[^"]*" target="_blank">`[^`]+`</a>)',
            f'### 🌀 Current Pulse Log ⟳ ChronoHex ⟐ <a href="https://lexemancy.com/" target="_blank">`{chronotonic}`</a>',
            readme_content
        )
        
        with readme_path.open("w", encoding="utf-8") as f:
            f.write(updated_readme)
        
        print(f"✅ README.md updated with chronohex: {chronotonic}")
    except Exception as e:
        print(f"⚠️ Failed to update README.md: {e}")

    # === ARCHIVE DAILY LOG + REBUILD INDEX ===
    logs_dir = output_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    logs_link_html_archive = '<p><a href="index.html">See past logs :: ></a></p>'
    archive_html = (
        html_content
        .replace('href="assets/theme.css"', 'href="../assets/theme.css"')
        .replace(f'href="assets/{stylesheet}"', f'href="../assets/{stylesheet}"')
        .replace('href="assets/index.ico"', 'href="../assets/index.ico"')
        .replace('src="assets/recursive-log-banner.mp4"', 'src="../assets/recursive-log-banner.mp4"')
        .replace(logs_link_html, logs_link_html_archive, 1)
    )

    log_path = logs_dir / f"{log_date}.html"
    with log_path.open("w", encoding="utf-8") as f:
        f.write(archive_html)
        if not archive_html.endswith("\n"):
            f.write("\n")

    existing_dates = []
    for p in logs_dir.glob("*.html"):
        if p.name == "index.html":
            continue
        stem = p.stem
        try:
            datetime.strptime(stem, "%Y-%m-%d")
        except ValueError:
            continue
        existing_dates.append(stem)

    existing_dates = sorted(set(existing_dates), reverse=True)
    index_html = render_logs_index_html(existing_dates, logs_dir, pulse_data["icon_tag"])
    index_path = REPO_ROOT / "logs-index.html"
    with index_path.open("w", encoding="utf-8") as f:
        f.write(index_html)
        if not index_html.endswith("\n"):
            f.write("\n")

    # === GIT COMMIT AND PUSH ===
    if os.environ.get("SKIP_GIT_PUSH") == "1":
        print("⚠️ Skipping git operations (test mode)")
    else:
        import subprocess
        try:
            # Stage all changes
            subprocess.run(["git", "add", "-A"], cwd=REPO_ROOT, check=True, capture_output=True)
            
            # Commit with chronohex in message
            commit_msg = f"🌀 Pulse update ⟳ {chronotonic}"
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=REPO_ROOT, check=True, capture_output=True)
            
            # Push to origin
            subprocess.run(["git", "push"], cwd=REPO_ROOT, check=True, capture_output=True)
            
            print(f"✅ Changes committed and pushed: {commit_msg}")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Git operation failed: {e}")
            # Don't exit - page was updated successfully even if git fails


if __name__ == "__main__":
    main()
