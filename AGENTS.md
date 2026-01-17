# Agent Documentation: Recursive Pulse Log System

## Overview
This repository generates a daily-updated personal homepage at `https://lexemancy.com/` using LLM-generated mystical/technical content. The system runs automatically via Windows Task Scheduler at 2:24 AM PST, generating fresh pulse content, updating files, and pushing to GitHub Pages.

## Architecture

### Core Components
- **`src/github_status_rotator.py`**: Main orchestrator. Generates pulse content, builds data dict, renders HTML via template, archives logs, commits and pushes changes.
- **`src/pulse_generator.py`**: LLM interface for generating mystical pulse field content. Samples from seed + cache examples for recursive feedback.
- **`src/template_renderer.py`**: Modular template engine. Loads templates and renders with `{{variable}}` substitution.
- **`src/esotericons.py`**: Icon library that fetches random esoteric icons from GitHub for daily divination.
- **`src/test_rotator.py`**: Safe test harness that runs generation in temp directory without git operations.
- **`templates/default.html`**: Main HTML template with `{{variable}}` placeholders for content injection.
- **`logs/pulses/*_cache.txt`**: Recursive feedback caches. LLM outputs append here and feed back as examples (grows indefinitely).
- **`logs/esotericons_cache.json`**: Cached icon list from esotericons repository (refreshed to exclude blurry multi-resolution variants).

### Output Structure
```
root/
├── index.html                    # Main homepage (Pulse Log - rendered from templates/default.html)
├── about.html                    # About page (rendered with pulse data)
├── projects.html                 # Projects page (rendered with pulse data)
├── utils.html                    # Utils page (rendered with pulse data)
├── zalgo-lexigon.html            # Zalgo text transformer (rendered with pulse data)
├── palette-mutator.html          # Color palette tool (rendered with pulse data)
├── paneudaemonium.html           # Paneudæmonium portal (static, own styles)
├── mondevour.html                # Mondevour page (static, own styles)
├── pulse.json                    # Structured pulse data (all fields for consumption)
├── README.md                     # Profile README with chronohex link
├── .env                          # Local LLM config (tracked for documentation)
├── templates/
│   └── default.html              # Main template with {{variable}} placeholders
├── logs/
│   ├── index.html                # Archive index with divination icons (teal header)
│   ├── YYYY-MM-DD.html           # Daily snapshots (one per day, overwritten)
│   ├── esotericons_cache.json    # Cached icon list (clean .ico and .svg only)
│   └── pulses/
│       ├── status_cache.txt      # Recursive feedback caches
│       ├── quote_cache.txt       # (seed + cache sections)
│       ├── glyph_cache.txt
│       ├── subject_cache.txt
│       ├── echo_cache.txt
│       ├── mode_cache.txt
│       └── end_quote_cache.txt
└── assets/
    ├── theme.css                 # Generated theme variables
    ├── style.css                 # Main stylesheet with navigation panel
    └── *.ico, *.mp4, *.svg       # Static assets
```

## Configuration

### `config/index.md`
**Purpose**: Human-readable configuration template for communicating page structure, content, and link changes to agents.

**Use this file when:**
- Modifying page layout or content structure
- Adding/removing/updating project links
- Changing text content or messaging
- Documenting intended page behavior

**Do NOT use for:**
- Direct CSS modifications (use `assets/style.css`)
- Theme color changes (use `config/style-config.yaml`)

### `config/style-config.yaml`
**Purpose**: Direct configuration of page elements without touching CSS.

**Structure:**
```yaml
projects:
  - name: "Project Name"
    github: "username/repo"
    sigil: "🜏"
    end_sigil: "🜄"  # Dyadic pair for visual closure
    color: "#f38ba8"  # Optional: project-specific color
    local_path: "subpath"  # Optional: for local links

theme:
  page_background: "#0d1117"
  frame_shadow: "0 0 25px 5px rgba(170, 120, 255, 0.25), inset 0 0 15px 2px rgba(136, 165, 255, 0.15)"
  link_color: "#eba0ac"      # Catppuccin Mocha maroon
  strong_color: "#89b4fa"    # Catppuccin Mocha blue
```

**Use this file when:**
- Adding/removing projects from the homepage
- Changing project colors, sigils, or dyadic pairs
- Modifying theme variables (background, shadows, link colors)
- Configuring project links (GitHub or local paths)

## Pulse Generation Process

### 1. LLM Warmup (Fast-Fail)
```python
# Verifies LLM is reachable before proceeding
# Exits immediately if configured but unreachable
# No silent fallback - enforces invariants
```

### 2. Parallel Field Generation
Generates 7 pulse fields concurrently (max 2 workers):
- `status`: Current status message
- `quote`: Antenna quote (mystical/technical)
- `glyph`: Cryptoglyph description (glyphbraid)
- `subject`: Subject identifier (zalgo-transformed before ⊚)
- `echo`: Echo fragment classification
- `mode`: Mode description
- `end_quote`: Closing quote

Each field:
1. Samples 5 random from seed section + up to 5 from cache section (10 total examples)
2. Sends to LLM with aesthetic-matching prompt (temperature 1.2 for variation)
3. Appends generated output to cache section (recursive feedback loop)
4. Falls back to batch cycling if LLM fails

**Cache Format:**
```
<-- slice: seed-->
seed example 1
seed example 2
<-- slice: cache-->
generated output 1
generated output 2
```

### 3. Icon Selection & Data Structuring
- Fetches random esotericon from GitHub (true random for divination)
- Creates chronohex: last 6 chars of `hex(time.time_ns())`
- Splits chronohex into individual characters for rainbow coloring (chronohex_0 through chronohex_5)
- Builds `pulse_data` dict with all pulse fields (status, quote, subject, mode, etc.) + icon URL
- Writes `pulse.json` for structured data consumption
- Updates `README.md` with chronohex link to lexemancy.com

### 4. Template Rendering & Static Page Updates
- Loads `templates/default.html` (contains `{{variable}}` placeholders)
- Renders HTML by substituting `{{variable}}` with values from `pulse_data`
- Writes `index.html` with fresh pulse content and icon
- **Renders static pages with pulse data**:
  - `about.html`: Gets icon_tag, status, timestamp, mode, class_disp_html, end_quote
  - `projects.html`: Gets icon_tag
  - `utils.html`: Gets icon_tag
  - `zalgo-lexigon.html`: Gets icon_tag
  - `palette-mutator.html`: Gets icon_tag
  - `logs/index.html`: Gets icon_tag (via render_logs_index_html function)
- **Icon syncing**: All pages share the same daily divination icon for unified aesthetic

### 5. Log Archiving & Index Rebuild
- Archives rendered HTML to `logs/YYYY-MM-DD.html` (rewrite paths for ../assets/)
- Scans `logs/` for all date-formatted HTML files
- Extracts icon URL from each archived log's `<link rel="icon" href="...">` tag
- Rebuilds `logs/index.html` with all dates + their divination icons (teal header #94e2d5)

### 6. Git Autopush
```bash
git add -A
git commit -m "🌀 Pulse update ⟳ {chronohex}"
git push
```

**IMPORTANT**: ALL commits should go through the rotator. Never commit manually.

**Why:**
- **Clean commit history**: Every commit follows the same format (`🌀 Pulse update ⟳ {chronohex}`)
- **Deterministic chronohex IDs**: Timestamp-based identifiers for each pulse
- **Atomic updates**: All changes (HTML, README, logs, caches) committed together
- **No mixed intent**: Commits represent complete pulse generations, not piecemeal edits

**To stage changes for the next pulse:**
- Edit configuration files (`config/*.yaml`, seed sections in caches)
- Edit source code (`src/*.py`, `assets/style.css`)
- Changes will be automatically committed on next rotator run

**Never do:**
- Manual `git commit` commands
- Separate commits for config vs code changes
- Commits outside the rotator's automated flow

## LLM Configuration

### Environment Variables (`.env` in repo root)
```bash
LLM_PROVIDER=lmstudio
LLM_BASE_URL=http://localhost:1234/v1
LLM_MODEL=gpt-oss-20b-heretic
LLM_API_KEY=  # Optional for LMStudio, required for OpenRouter
```

**Note:** `.env` is tracked in git to document working model configuration. Use `secrets.env` for API keys (not tracked).

### Generation Parameters
- **Temperature**: 1.2 (high variation for recursive diversity)
- **Sample size**: 5 seed + up to 5 cache examples (10 total)
- **No `max_tokens`**: Let LLM generate naturally (covenant principle)
- **Timeout**: 60s per request
- **Parallel workers**: 2 (LMStudio/OpenRouter compatible)

## Scheduled Task

### Windows Task Scheduler
- **Task Name**: `PulseLogUpdater`
- **Schedule**: Daily at 2:24 AM PST
- **Command**: `python src/github_status_rotator.py`
- **Working Directory**: `C:\Users\synta.ZK-ZRRH\.dev\SyntaxAsSpiral`
- **Wake to run**: Enabled
- **Timeout**: 10 minutes

### Manual Trigger
```powershell
schtasks /run /tn "PulseLogUpdater"
```

## Path Conventions

### Asset References
- **Root `index.html`**: `assets/*`
- **Logs `logs/*.html`**: `../assets/*`
- **All paths relative**: No absolute URLs for assets
- **Navigation links**: Root-relative paths (`/`) for proper subdirectory navigation

### Project Links
- **GitHub projects**: `https://github.com/{github}`
- **Local projects**: `{local_path}` (relative to root)

## Navigation System

### Rainbow Catppuccin Side Panel
- **Hamburger menu** (top-right): Opens slide-in navigation panel from right
- **Click-off-to-close**: Overlay dismisses panel when clicking outside
- **localStorage persistence**: Panel state persists across page navigation
- **Rainbow tabs** with Catppuccin Mocha colors:
  - 🌀 Pulse Log (Red #f38ba8) → `index.html`
  - 🜏 About (Peach #fab387) → `about.html`
  - ⟁ Projects (Yellow #f9e2af) → `projects.html`
  - ⚗️ Utils (Green #a6e3a1) → `utils.html`
  - 🜃 Paneudæmonium (Sapphire #74c7ec) → `paneudaemonium.html`
  - 🎭 Mondevour (Lavender #b4befe) → `mondevour.html`
- **Active tab styling**: Gradient mutation effect (brightness 1.2, saturate 1.3)
- **Page headers**: Match their tab colors for visual consistency

### Special Pages
- **Paneudæmonium**: Keeps own stylesheet (`assets/paneudaemonium/style.css`), not inheriting main styles
- **Mondevour**: Keeps own inline styles and character, footer links back to Paneudæmonium

## Design Principles

### Fast-Fail Enforcement
- LLM configured but unreachable = immediate exit
- No silent degradation to batch cycling
- **NO FALLBACK TO CACHE/RANDOM SELECTION** - if LLM fails, the page does NOT update
- Timestamp on page = health indicator (stale timestamp = visible failure signal)
- Read-only startup health checks (no data creation for smoke tests)
- **NEVER hide failure behind "graceful degradation"** - failure must be visible and loud
- The absence of a fresh pulse IS the error message to the operator

### Recursive Feedback Loop
- LLM outputs append to cache files (no trimming - grows indefinitely)
- Cache examples feed back into next generation
- Creates self-evolving aesthetic over time
- Text format preferred over JSONL (human-readable, git-friendly diffs)

### Deterministic Behavior
- Chronohex = deterministic timestamp-based ID
- One log per day (overwrites on multiple runs same day)
- Icons truly random (not cycling) for divination purposes
- Stable ordering in archive index (reverse chronological)

### Bespoke Optimization
- Personal system, not enterprise-scale
- Disposable software: optimize for beauty over maintainability
- Direct solutions over frameworks
- Final-state surgery: no compatibility shims or legacy fallbacks

### Clean Commit History
- All commits flow through the rotator's automated process
- Uniform commit messages: `🌀 Pulse update ⟳ {chronohex}`
- Each commit represents a complete pulse generation (atomic)
- No manual commits, no mixed-intent changes
- Git history becomes a clean temporal log of pulse states

## Agent Instructions

### Commit Protocol
**CRITICAL**: Never commit changes manually. All commits go through the rotator.

**Workflow:**
1. Make your changes (config, source code, seed sections)
2. Let the rotator commit everything together on next run
3. This keeps commit history clean with uniform `🌀 Pulse update ⟳ {chronohex}` messages

**Exception**: If working on new features that require testing multiple iterations, stage changes normally but do not commit until ready. Then run the rotator once to commit everything atomically.

### When modifying page content:
1. Check `config/index.md` for structure documentation
2. Update `config/style-config.yaml` for project/theme changes
3. Modify `src/github_status_rotator.py` for HTML generation logic
4. Never edit `index.html`, `README.md`, or rendered static pages directly (auto-generated)
5. Edit source HTML files (about.html, projects.html, etc.) to add `{{variable}}` placeholders
6. Add files to `static_pages` list in rotator if they need pulse data injection
7. Never commit manually - let the rotator handle it

### When modifying navigation:
1. Edit `assets/style.css` for panel styling and tab colors
2. Update navigation HTML in each page's source file
3. Use root-relative paths (`/`) for all navigation links
4. Match page header colors to their tab colors for consistency
5. Paneudæmonium and Mondevour keep their own styles (don't inherit main navigation)

### When adding new pulse fields:
1. Create cache file in `logs/pulses/{field}_cache.txt` with seed/cache sections
2. Add field to `FIELD_MAPPINGS` in `pulse_generator.py`
3. Generate field in `github_status_rotator.py` and add to `pulse_data` dict
4. Add `{{field_name}}` placeholder to `templates/default.html` where desired
5. Renderer automatically substitutes `{{field_name}}` with the value from `pulse_data`

### When tuning prompts:
- Run `python src/pulse_generator.py` to test LLM generation without HTML/git
- Adjust temperature in `pulse_generator.py` for more/less variation
- Add vocabulary examples to seed sections in cache files
- Review cache sections to see recursive evolution

### When debugging:
- Check LLM server logs at `http://localhost:1234`
- Verify `.env` configuration in repo root
- Test LLM only: `python src/pulse_generator.py`
- Test template rendering: `python src/template_renderer.py pulse.json [template_name]`
- Test full generation (no git): `python src/test_rotator.py`
- Test with git push: `python src/github_status_rotator.py`
- Check git status for uncommitted changes
- Verify esotericons cache: `python -c "from esotericons import get_icon_list; get_icon_list(refresh=True)"` to refresh
- Inspect pulse data: `cat pulse.json` to see all generated fields

## File Modification Rules

### Auto-Generated (DO NOT EDIT MANUALLY):
- `index.html` (rendered from templates/default.html)
- `pulse.json`
- `README.md`
- `logs/*.html` (daily archives)
- `logs/index.html` (archive index)
- `assets/theme.css`
- `logs/esotericons_cache.json`
- Cache sections in `logs/pulses/*_cache.txt` (LLM appends here)

### Safe to Edit (Source Files):
- `config/index.md`
- `config/style-config.yaml`
- `config/zalgo-config.json`
- `assets/style.css` (navigation and main styles)
- `assets/paneudaemonium/style.css` (Paneudæmonium-specific styles)
- Seed sections in `logs/pulses/*_cache.txt`
- `src/*.py`
- `templates/*.html` (create alternates, modify existing)
- `about.html`, `projects.html`, `utils.html` (source files with {{placeholders}})
- `zalgo-lexigon.html`, `palette-mutator.html` (utility pages)
- `paneudaemonium.html`, `mondevour.html` (special pages with own styles)
- `.env` (local LLM config)

### Never Track:
- `secrets.env` (API keys)

## Template System

### Architecture
The system decouples **content generation** from **presentation**:
- **Content**: Generated by `pulse_generator.py` + `github_status_rotator.py` → `pulse.json`
- **Presentation**: Consumed by `template_renderer.py` from `templates/*.html`
- **Independence**: Change templates without touching generation logic, and vice versa

### Creating Alternate Templates
You can create multiple templates without modifying the rotator:

1. Create `templates/{name}.html` with `{{variable}}` placeholders
2. Include variables from `pulse_data` dict (see rotator lines 567-582)
3. Call `render_template("{name}", pulse_data)` to render
4. No generation logic changes needed

**Available variables for templates:**
- `chronotonic`, `chronohex`, `timestamp`, `stylesheet`, `icon_tag`
- `chronohex_0` through `chronohex_5` (individual rainbow-colored characters)
- `quote`, `subject_font`, `subject_zalgo`, `braid`
- `status`, `mode`, `class_disp_html`, `end_quote`
- `projects_html`, `logs_link_html`

### Template Syntax
Simple regex-based substitution—no Jinja2 or complex logic:
```html
<h1>{{chronotonic}}</h1>
<p>Status: {{status}}</p>
```

**Complex rendering** (loops, conditionals): Pre-render in rotator and pass as strings (e.g., `projects_html`)

## Special Features

### Esotericon Divination System
- Random icon selected daily from `https://github.com/SyntaxAsSpiral/esotericons`
- Icon URL baked into daily archive HTML
- **Icon syncing**: Same icon injected across all pages (index, about, projects, utils, zalgo-lexigon, palette-mutator, logs/index)
- Logs index displays each day's icon as visual tarot/rune deck
- True random selection (not cycling) for divination purposes
- Fallback to `assets/index.ico` if fetch fails

### Rainbow Chronohex Display
- 6-character chronohex split into individual spans
- Each character colored with Catppuccin rainbow:
  - Character 0: Red (#f38ba8)
  - Character 1: Peach (#fab387)
  - Character 2: Yellow (#f9e2af)
  - Character 3: Green (#a6e3a1)
  - Character 4: Sapphire (#74c7ec)
  - Character 5: Lavender (#b4befe)
- Naturally includes letters (a-f) from hex encoding
- All-digit codes are valid but rare

### Zalgo Text Transformation
- Applied to subject IDs (only text before ⊚ symbol)
- Configured via `config/zalgo-config.json`
- Supports multiple styles: rootglow, classic
- Intensity and mark types configurable

### Theme System
- CSS variables generated from `config/style-config.yaml`
- Written to `assets/theme.css` on each run
- Supports: page background, frame shadow, link color, strong color
- Project-specific colors apply only to project name links

## GitHub Pages Configuration
- **Source**: `main` branch, root `/`
- **Custom domain**: `lexemancy.com`
- **HTTPS**: Enforced
- **Build type**: Legacy (not Actions)

## IDE Task Configuration

### Available Tasks (`.vscode/tasks.json`)
- **Pulse: Generate & Push** (default build): Full generation with git push
- **Pulse: Test Generation** (default test): Safe test without git operations
- **Pulse: Test LLM Only**: Tests LLM generation without HTML

Use `SKIP_GIT_PUSH=1` environment variable to disable git operations in any script.

---
