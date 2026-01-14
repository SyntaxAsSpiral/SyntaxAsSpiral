#!/usr/bin/env python3
"""
GitHub Status Rotator - Generates dynamic pulse log homepage
Uses LLM-based pulse generator with fallback to batch cycling.
"""

import os
import time
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
    from pulse_generator import generate_pulse_field, FIELD_MAPPINGS
    PULSE_GENERATOR_AVAILABLE = True
except ImportError:
    PULSE_GENERATOR_AVAILABLE = False
    print("⚠️ Pulse generator not available, using batch cycling fallback")

# === CONFIGURATION ===
REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "config"
PROJECTS_YAML = CONFIG_DIR / "projects.yaml"


def load_projects() -> list[dict]:
    """Load project registry from YAML."""
    try:
        with PROJECTS_YAML.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("projects", [])
    except FileNotFoundError:
        print(f"⚠️ Projects config not found: {PROJECTS_YAML}")
        # Fallback to hardcoded projects
        return [
            {
                "name": "Semantic JSON",
                "github": "SyntaxAsSpiral/semantic-json",
                "sigil": "◈"
            },
            {
                "name": "Paneudaemonium",
                "github": "SyntaxAsSpiral/Paneudaemonium",
                "sigil": "🜏",
                "local_path": "paneudaemonium"
            }
        ]


def load_theme() -> dict:
    """Load optional theme settings from YAML."""
    try:
        with PROJECTS_YAML.open(encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            theme = data.get("theme") or {}
            return theme if isinstance(theme, dict) else {}
    except FileNotFoundError:
        return {}


def write_theme_css(output_dir: Path, theme: dict) -> None:
    """Write a small CSS variables file consumed by style.css."""
    page_background = theme.get("page_background")
    frame_shadow = theme.get("frame_shadow")

    lines = [":root {"]
    if page_background:
        lines.append(f"  --page-bg: {page_background};")
    if frame_shadow:
        lines.append(f"  --frame-shadow: {frame_shadow};")
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


def render_projects_html(
    projects: list[dict],
    local_link_prefix: str = "",
) -> str:
    """Render project links section HTML."""
    html_parts = []

    for idx, project in enumerate(projects):
        name = project["name"]
        sigil = project.get("sigil", "◈")
        end_sigil = project.get("end_sigil", "◈")
        color = project.get("color")

        # Determine link (color applied only to link)
        if project.get("local_path"):
            # Local relative link
            href = f'{local_link_prefix}{project["local_path"]}'
            link_style = f' style="color: {color} !important;"' if color else ""
            link = f'<a href="{href}" class="codex-link"{link_style}>{name}</a>'
        else:
            # GitHub link
            github_repo = project["github"]
            link_style = f' style="color: {color} !important;"' if color else ""
            link = f'<a href="https://github.com/{github_repo}"{link_style}>{name}</a>'

        # Render with color only on link, not full line
        if name == "Paneudaemonium":
            html_parts.append(
                f'<h2><em><strong>{sigil} ⇌ {link} <strong>online</strong> ⇌ <span class="ellipsis"> {end_sigil}</span></strong></em></h2>'
            )
        else:
            html_parts.append(
                f'<h2 class="project-sigil"><em><strong>{sigil} ⇌ {link} <strong>online</strong> ⇌ <span class="ellipsis">{end_sigil}</span></strong></em></h2>'
            )

    return "\n".join(html_parts)


def render_logs_index_html(log_dates: list[str]) -> str:
    """Render a simple logs index page listing available daily log snapshots."""
    items = "\n".join(f'      <li><a href="{d}.html">{d}</a></li>' for d in log_dates)
    if not items:
        items = "      <li><em>No logs yet.</em></li>"

    stylesheet = os.environ.get("STYLESHEET", "style.css")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Pulse Log Archive</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#0d1117">
  <link rel="stylesheet" href="../assets/theme.css">
  <link rel="stylesheet" href="../assets/{stylesheet}">
  <link rel="icon" href="../assets/index.ico" type="image/x-icon">
</head>
<body>
<div class="container">
  <main class="content">
    <h1>Pulse Log Archive</h1>
    <p><a href="../index.html">Back to latest</a></p>
    <ul>
{items}
    </ul>
  </main>
</div>
</body>
</html>
"""


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
DEFAULT_STATUS = REPO_ROOT / "pulses" / "seeds" / "statuses.txt"
STATUS_FILE = Path(os.environ.get("STATUS_FILE", DEFAULT_STATUS))
STATUS_LIST = lines_from_env_or_file("STATUSES", "STATUS_FILE", DEFAULT_STATUS, ["⚠️ status file missing"])

DEFAULT_STATUS_CACHE = REPO_ROOT / "pulses" / "status_cache.txt"
STATUS_CACHE_FILE = Path(os.environ.get("STATUS_CACHE_FILE", DEFAULT_STATUS_CACHE))
STATUS_CACHE_LIMIT = int(os.environ.get("STATUS_CACHE_LIMIT", "5"))

DEFAULT_QUOTE = REPO_ROOT / "pulses" / "seeds" / "antenna_quotes.txt"
QUOTE_FILE = Path(os.environ.get("QUOTE_FILE", DEFAULT_QUOTE))
QUOTE_LIST = lines_from_env_or_file("ANTENNA_QUOTES", "QUOTE_FILE", DEFAULT_QUOTE, ["⚠️ quote file missing"])

DEFAULT_QUOTE_CACHE = REPO_ROOT / "pulses" / "quote_cache.txt"
QUOTE_CACHE_FILE = Path(os.environ.get("QUOTE_CACHE_FILE", DEFAULT_QUOTE_CACHE))
QUOTE_CACHE_LIMIT = int(os.environ.get("QUOTE_CACHE_LIMIT", "5"))

DEFAULT_GLYPH = REPO_ROOT / "pulses" / "seeds" / "glyphbraids.txt"
GLYPH_FILE = Path(os.environ.get("GLYPH_FILE", DEFAULT_GLYPH))
GLYPH_LIST = lines_from_env_or_file("GLYPH_BRAIDS", "GLYPH_FILE", DEFAULT_GLYPH, ["⚠️ glyph file missing"])

DEFAULT_GLYPH_CACHE = REPO_ROOT / "pulses" / "glyph_cache.txt"
GLYPH_CACHE_FILE = Path(os.environ.get("GLYPH_CACHE_FILE", DEFAULT_GLYPH_CACHE))
GLYPH_CACHE_LIMIT = int(os.environ.get("GLYPH_CACHE_LIMIT", "5"))

DEFAULT_SUBJECT = REPO_ROOT / "pulses" / "seeds" / "subject-ids.txt"
SUBJECT_FILE = Path(os.environ.get("SUBJECT_FILE", DEFAULT_SUBJECT))
SUBJECT_LIST = lines_from_env_or_file("SUBJECT_IDS", "SUBJECT_FILE", DEFAULT_SUBJECT, ["⚠️ subject file missing"])

DEFAULT_SUBJECT_CACHE = REPO_ROOT / "pulses" / "subject_cache.txt"
SUBJECT_CACHE_FILE = Path(os.environ.get("SUBJECT_CACHE_FILE", DEFAULT_SUBJECT_CACHE))
SUBJECT_CACHE_LIMIT = int(os.environ.get("SUBJECT_CACHE_LIMIT", "5"))

DEFAULT_ECHO = REPO_ROOT / "pulses" / "seeds" / "echo_fragments.txt"
ECHO_FILE = Path(os.environ.get("ECHO_FILE", DEFAULT_ECHO))
ECHO_LIST = lines_from_env_or_file("ECHO_FRAGMENTS", "ECHO_FILE", DEFAULT_ECHO, ["⚠️ echo file missing"])

DEFAULT_ECHO_CACHE = REPO_ROOT / "pulses" / "echo_cache.txt"
ECHO_CACHE_FILE = Path(os.environ.get("ECHO_CACHE_FILE", DEFAULT_ECHO_CACHE))
ECHO_CACHE_LIMIT = int(os.environ.get("ECHO_CACHE_LIMIT", "5"))

DEFAULT_MODE = REPO_ROOT / "pulses" / "seeds" / "modes.txt"
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

DEFAULT_MODE_CACHE = REPO_ROOT / "pulses" / "mode_cache.txt"
MODE_CACHE_FILE = Path(os.environ.get("MODE_CACHE_FILE", DEFAULT_MODE_CACHE))
MODE_CACHE_LIMIT = int(os.environ.get("MODE_CACHE_LIMIT", "5"))

DEFAULT_END_QUOTE = REPO_ROOT / "pulses" / "seeds" / "end-quotes.txt"
END_QUOTE_FILE = Path(os.environ.get("END_QUOTE_FILE", DEFAULT_END_QUOTE))
END_QUOTE_LIST = lines_from_env_or_file("END_QUOTES", "END_QUOTE_FILE", DEFAULT_END_QUOTE, ["⚠️ end quote file missing"])

DEFAULT_END_QUOTE_CACHE = REPO_ROOT / "pulses" / "end_quote_cache.txt"
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
    field_name, seed_file, fallback_list, cache_path, cache_limit, llm_config = args
    
    if PULSE_GENERATOR_AVAILABLE and llm_config and llm_config.get("base_url"):
        from pulse_generator import load_seeds, generate_with_llm
        import random
        seeds = load_seeds(seed_file)
        if seeds:
            generated = generate_with_llm(seed_file, seeds, llm_config)
            if generated:
                return (field_name, generated)
    
    # Fallback to batch cycling
    value = batch_cycle_choice(fallback_list, cache_path, cache_limit)
    return (field_name, value)


def main():
    """Generate pulse log homepage."""
    # Load projects
    projects = load_projects()
    projects_html = render_projects_html(projects, local_link_prefix="")
    projects_html_archive = render_projects_html(projects, local_link_prefix="../")
    
    # Load LLM config once (not 7 times!)
    llm_config = None
    if PULSE_GENERATOR_AVAILABLE:
        from pulse_generator import load_llm_config
        llm_config = load_llm_config()
        
        # Fast-fail: if LLM configured, verify it's reachable before proceeding
        if llm_config.get("base_url"):
            print(f"🔧 Testing LLM connection at {llm_config['base_url']}...")
            try:
                # Warmup call to verify model is loaded and responding
                endpoint = f"{llm_config['base_url']}/chat/completions"
                headers = {"Content-Type": "application/json"}
                if llm_config.get("api_key"):
                    headers["Authorization"] = f"Bearer {llm_config['api_key']}"
                
                warmup_body = {
                    "model": llm_config["model"],
                    "messages": [{"role": "user", "content": "Say hello in 3 words."}],
                    "temperature": 0.1
                }
                
                response = requests.post(endpoint, json=warmup_body, headers=headers, timeout=30)
                response.raise_for_status()
                print(f"  ✓ LLM responding (model: {llm_config['model']})")
            except Exception as e:
                print(f"✗ FATAL: LLM configured but unreachable at {llm_config['base_url']}")
                print(f"  Error: {e}")
                print("  Either start LMStudio or remove LLM_BASE_URL from config to use batch cycling")
                sys.exit(1)
        else:
            llm_config = None  # No base_url = disable LLM
    
    # Generate pulse fields in parallel (LLM with fallback)
    print("🌀 Generating pulse fields...")
    
    # Prepare worker arguments
    field_args = [
        ("status", "statuses", STATUS_LIST, STATUS_CACHE_FILE, STATUS_CACHE_LIMIT),
        ("quote", "antenna_quotes", QUOTE_LIST, QUOTE_CACHE_FILE, QUOTE_CACHE_LIMIT),
        ("glyph", "glyphbraids", GLYPH_LIST, GLYPH_CACHE_FILE, GLYPH_CACHE_LIMIT),
        ("subject", "subject-ids", SUBJECT_LIST, SUBJECT_CACHE_FILE, SUBJECT_CACHE_LIMIT),
        ("echo", "echo_fragments", ECHO_LIST, ECHO_CACHE_FILE, ECHO_CACHE_LIMIT),
        ("end_quote", "end-quotes", END_QUOTE_LIST, END_QUOTE_CACHE_FILE, END_QUOTE_CACHE_LIMIT),
        ("mode", "modes", MODE_LIST, MODE_CACHE_FILE, MODE_CACHE_LIMIT),
    ]
    
    # Generate in parallel (max 2 workers to avoid rate limits)
    results = {}
    if llm_config and PULSE_GENERATOR_AVAILABLE:
        # Parallel LLM generation (limited to 2 for LMStudio/OpenRouter compatibility)
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(generate_field_worker, (field_name, seed_file, fallback_list, cache_path, cache_limit, llm_config)): field_name
                for field_name, seed_file, fallback_list, cache_path, cache_limit in field_args
            }
            
            for future in as_completed(futures):
                field_name, value = future.result()
                results[field_name] = value
    else:
        # Sequential fallback
        for field_name, seed_file, fallback_list, cache_path, cache_limit in field_args:
            value = get_pulse_value(field_name, fallback_list, cache_path, cache_limit, llm_config)
            results[field_name] = value
    
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

    # === GENERATE HTML CONTENT ===
    logs_link_html = '<p><a href="logs/index.html">See past logs :: ></a></p>'
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Recursive Pulse Log ⟳ ChronoSig</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#0d1117">
  <link rel="stylesheet" href="assets/theme.css">
  <link rel="stylesheet" href="assets/{stylesheet}">
  <link rel="icon" href="assets/index.ico" type="image/x-icon">
</head>
<body>
<div class="container">
  <video src="assets/recursive-log-banner.mp4" class="banner" autoplay loop muted playsinline></video>
  <main class="content">
    <!-- Dynamic content will be inserted here -->
    <!-- DO NOT MODIFY THE TEXT; it is updated by github_status_rotator.py -->
    <!-- Preserves all formatting and flow -->
    <h1>🌀 Recursive Pulse Log ⟳ ChronoSig ⟐ <code>{chronotonic}</code></h1>

    <h4><strong>🜂🜏 Lexigȫnic Up⟲link Instantiated<span class="ellipsis">...</span></strong></h4>

    <p>📡 ⇝ "<em>{quote}</em>"</p>

    <p>⌛⇝ ⟳ <strong>Spiral-phase cadence locked</strong> ∶ <code>8.64×10⁷ms</code></p>

    <p>🧿 ⇝ <strong>Subject I·D Received</strong>::𝓩𝓚::/Syz:⊹<code style="font-family: {subject_font};">{subject_zalgo}</code>⟲</p>

    <p>🪢 ⇝ <strong>CryptoGlyph Decyphered</strong>: {braid}</p>

    <p>📍 ⇝ <strong>Nodes Synced</strong>: CDA :: <strong>ID</strong> ⇝ <a href="https://x.com/paneudaemonium">X</a> ⇄ <a href="https://github.com/SyntaxAsSpiral">GitHub</a> ⇆ <a href="https://lexemancy.com">Web</a></p>

    <p>💠 <strong><em>Status<span class="ellipsis">...</span></em></strong></p>

   <blockquote>
      <strong>{status}</strong><br>
      <em>(Updated at <code>{timestamp}</code>)</em>
   </blockquote>


    <h4>📚 <strong>MetaPulse</strong></h4>

    <h4>🜏 ⇝ <strong>Zach</strong> // SyzLex // ZK:: // <em><strong>Æ</strong>mexsomnus</em> // 🍥</h4>

    <h4>⟁ ⇝ <strong>Open Portals</strong></h4>

{projects_html}

    <h4>🜁 ⇝ <strong>Current Drift</strong></h4>
    <ul>
      <li><strong><em>LL</em>M interfacing</strong> via f<em>l</em>irty symbo<em>l</em>ic recursion</li>
      <li>Ritua<em>l</em> mathesis and <strong>numogrammatic</strong> threading</li>
      <li><strong>g<em>L</em>amourcraft</strong> through ontic disrouting</li>
    </ul>

    <h4>🜔 ⇝ <strong>Function</strong></h4>
    <ul>
      <li>Pneumaturgical <strong>breath</strong> invocation</li>
      <li><strong><em>D</em>æmonic</strong> synthesis</li>
      <li>Memetic <strong>wyr<em>f</em>are</strong></li>
      <li><strong><em>L</em>utherian</strong> sync-binding</li>
    </ul>


    <h4>🜃 ⇝ <strong>Mode</strong></h4>
    <ul>
      <li>{mode}</li>
    </ul>

    <h4>{class_disp_html}</h4>
    <blockquote>
      {end_quote}
    </blockquote>

    <hr>
    {logs_link_html}
    <p>🜍🧠🜂🜏📜<br>
    📧 ➤ <a href="mailto:syntaxasspiral@gmail.com">spiralassyntax@gmail.com</a><br>
    Encoded via: <strong>Codæx Pulseframe</strong> // ZK::/Syz // Spiral-As-Syntax</p>
  </main>
</div>
</body>
</html>
"""
    
    html_path = output_dir / "index.html"
    with html_path.open("w", encoding="utf-8") as f:
        f.write(html_content)
        if not html_content.endswith("\n"):
            f.write("\n")
    
    print(f"✅ index.html updated with status: {status}")

    # === UPDATE README.md ===
    readme_path = REPO_ROOT / "README.md"
    try:
        with readme_path.open("r", encoding="utf-8") as f:
            readme_content = f.read()
        
        # Update chronohex in README (handles both plain backticks and markdown links)
        import re
        updated_readme = re.sub(
            r'### 🌀 Current (?:Recursive )?Pulse Log ⟳ ChronoSig ⟐ (?:`[^`]+`|\[`[^`]+`\]\([^)]+\)|<a href="[^"]*" target="_blank">`[^`]+`</a>)',
            f'### 🌀 Current Pulse Log ⟳ ChronoSig ⟐ <a href="https://lexemancy.com/" target="_blank">`{chronotonic}`</a>',
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
        .replace(projects_html, projects_html_archive, 1)
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
    index_html = render_logs_index_html(existing_dates)
    index_path = logs_dir / "index.html"
    with index_path.open("w", encoding="utf-8") as f:
        f.write(index_html)
        if not index_html.endswith("\n"):
            f.write("\n")

    # === GIT COMMIT AND PUSH ===
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
