# Agent Documentation: Recursive Pulse Log System

## Overview
This repository generates a daily-updated personal homepage at `https://lexemancy.com/` using LLM-generated mystical/technical content. The system runs automatically via Windows Task Scheduler at 2:24 AM PST, generating fresh pulse content, updating files, and pushing to GitHub Pages.

## Architecture

### Core Components
- **`src/github_status_rotator.py`**: Main orchestrator. Generates pulse content, updates HTML/README, archives logs, commits and pushes changes.
- **`src/pulse_generator.py`**: LLM interface for generating mystical pulse field content. Samples from seed + cache examples for recursive feedback.
- **`src/esotericons.py`**: Icon library that fetches random esoteric icons from GitHub for daily divination.
- **`src/test_rotator.py`**: Safe test harness that runs generation in temp directory without git operations.
- **`logs/pulses/*_cache.txt`**: Recursive feedback caches. LLM outputs append here and feed back as examples (grows indefinitely).
- **`logs/esotericons_cache.json`**: Cached icon list from esotericons repository.

### Output Structure
```
root/
├── index.html                    # Main homepage (GitHub Pages entry point)
├── README.md                     # Profile README with chronohex link
├── .env                          # Local LLM config (tracked for documentation)
├── logs/
│   ├── index.html                # Archive index with divination icons
│   ├── YYYY-MM-DD.html           # Daily snapshots (one per day, overwritten)
│   ├── esotericons_cache.json    # Cached icon list
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
    ├── style.css                 # Main stylesheet
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

### 3. Icon Selection & HTML Generation
- Fetches random esotericon from GitHub (true random for divination)
- Generates `index.html` with fresh pulse content and icon
- Creates chronohex: last 6 chars of `hex(time.time_ns())`
- Updates `README.md` with chronohex link to lexemancy.com
- Archives daily snapshot to `logs/YYYY-MM-DD.html` (preserves icon URL)
- Rebuilds `logs/index.html` with all dates + their divination icons

### 4. Git Autopush
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

### Project Links
- **GitHub projects**: `https://github.com/{github}`
- **Local projects**: `{local_path}` (relative to root)

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
4. Never edit `index.html` or `README.md` directly (auto-generated)
5. Never commit manually - let the rotator handle it

### When adding new pulse fields:
1. Create cache file in `logs/pulses/{field}_cache.txt` with seed/cache sections
2. Add field to `FIELD_MAPPINGS` in `pulse_generator.py`
3. Add generation logic to `github_status_rotator.py`
4. Update HTML template with new field placeholder

### When tuning prompts:
- Run `python src/pulse_generator.py` to test LLM generation without HTML/git
- Adjust temperature in `pulse_generator.py` for more/less variation
- Add vocabulary examples to seed sections in cache files
- Review cache sections to see recursive evolution

### When debugging:
- Check LLM server logs at `http://localhost:1234`
- Verify `.env` configuration in repo root
- Test LLM only: `python src/pulse_generator.py`
- Test full generation (no git): `python src/test_rotator.py`
- Test with git push: `python src/github_status_rotator.py`
- Check git status for uncommitted changes
- Verify esotericons cache: `logs/esotericons_cache.json`

## File Modification Rules

### Auto-Generated (DO NOT EDIT MANUALLY):
- `index.html`
- `README.md`
- `logs/*.html`
- `assets/theme.css`
- `logs/esotericons_cache.json`
- Cache sections in `logs/pulses/*_cache.txt` (LLM appends here)

### Safe to Edit:
- `config/index.md`
- `config/style-config.yaml`
- `config/zalgo-config.json`
- `assets/style.css`
- Seed sections in `logs/pulses/*_cache.txt`
- `src/*.py`
- `.env` (local LLM config)

### Never Track:
- `secrets.env` (API keys)

## Special Features

### Esotericon Divination System
- Random icon selected daily from `https://github.com/SyntaxAsSpiral/esotericons`
- Icon URL baked into daily archive HTML
- Logs index displays each day's icon as visual tarot/rune deck
- True random selection (not cycling) for divination purposes
- Fallback to `assets/index.ico` if fetch fails

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
