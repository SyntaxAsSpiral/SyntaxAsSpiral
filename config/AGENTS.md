# Agent Documentation: Recursive Pulse Log System

## Overview
This repository generates a daily-updated personal homepage at `https://lexemancy.com/` using LLM-generated mystical/technical content. The system runs automatically via Windows Task Scheduler at 2:24 AM PST, generating fresh pulse content, updating files, and pushing to GitHub Pages.

## Architecture

### Core Components
- **`src/github_status_rotator.py`**: Main orchestrator. Generates pulse content, updates HTML/README, archives logs, commits and pushes changes.
- **`src/pulse_generator.py`**: LLM interface for generating mystical pulse field content using seed examples.
- **`src/seed_batch_caches.py`**: Utility for pre-seeding batch cycling caches (fallback mode).
- **`pulses/seeds/*.txt`**: Seed content files used as examples for LLM generation.
- **`pulses/*_cache.txt`**: Batch cycling caches (used when LLM unavailable).

### Output Structure
```
root/
├── index.html          # Main homepage (GitHub Pages entry point)
├── README.md           # Profile README with chronohex link
├── logs/
│   ├── index.html      # Archive index
│   └── YYYY-MM-DD.html # Daily snapshots (one per day, overwritten)
└── assets/
    ├── theme.css       # Generated theme variables
    ├── style.css       # Main stylesheet
    ├── *.ico, *.mp4    # Static assets
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
- Theme color changes (use `config/projects.yaml`)

### `config/projects.yaml`
**Purpose**: Direct configuration of page elements without touching CSS.

**Structure:**
```yaml
projects:
  - name: "Project Name"
    github: "username/repo"
    sigil: "🜏"
    color: "#f38ba8"  # Optional: project-specific color
    local_path: "subpath"  # Optional: for local links

theme:
  page_background: "#0d1117"
  frame_shadow: "0 0 20px rgba(0,0,0,0.5)"
```

**Use this file when:**
- Adding/removing projects from the homepage
- Changing project colors or sigils
- Modifying theme variables (background, shadows)
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
- `glyph`: Cryptoglyph description
- `subject`: Subject identifier
- `echo`: Echo fragment classification
- `mode`: Mode description
- `end_quote`: Closing quote

Each field:
1. Samples 5 random seeds from `pulses/seeds/{field}.txt`
2. Sends to LLM with aesthetic-matching prompt
3. Falls back to batch cycling if LLM fails

### 3. HTML Generation
- Generates `index.html` with fresh pulse content
- Creates chronohex: last 6 chars of `hex(time.time_ns())`
- Updates `README.md` with chronohex link
- Archives daily snapshot to `logs/YYYY-MM-DD.html`
- Rebuilds `logs/index.html` with all available dates

### 4. Git Autopush
```bash
git add -A
git commit -m "🌀 Pulse update ⟳ {chronohex}"
git push
```

## LLM Configuration

### Environment Variables (`.dev/.env`)
```bash
LLM_PROVIDER=lmstudio
LLM_BASE_URL=http://localhost:1234/v1
LLM_MODEL=gpt-oss-20b-heretic
LLM_API_KEY=  # Optional for LMStudio
```

### Generation Parameters
- **Temperature**: 0.8 (creative but coherent)
- **Sample size**: 5 seeds per field
- **No `max_tokens`**: Let LLM generate naturally
- **Timeout**: 60s per request

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
- Timestamp on page = health indicator

### Deterministic Behavior
- Chronohex = deterministic timestamp-based ID
- Stable seed sampling (random but reproducible)
- One log per day (overwrites on multiple runs)

### Bespoke Optimization
- Personal system, not enterprise-scale
- Disposable software: optimize for beauty over maintainability
- Direct solutions over frameworks

## Agent Instructions

### When modifying page content:
1. Check `config/index.md` for structure documentation
2. Update `config/projects.yaml` for project/theme changes
3. Modify `src/github_status_rotator.py` for HTML generation logic
4. Never edit `index.html` or `README.md` directly (auto-generated)

### When adding new pulse fields:
1. Create seed file in `pulses/seeds/{field}.txt`
2. Add field to `FIELD_MAPPINGS` in `pulse_generator.py`
3. Add generation logic to `github_status_rotator.py`
4. Update HTML template with new field placeholder

### When debugging:
- Check LLM server logs at `http://localhost:1234`
- Verify `.dev/.env` configuration
- Test with manual run: `python src/github_status_rotator.py`
- Check git status for uncommitted changes

## File Modification Rules

### Auto-Generated (DO NOT EDIT MANUALLY):
- `index.html`
- `README.md`
- `logs/*.html`
- `assets/theme.css`
- `pulses/*_cache.txt`

### Safe to Edit:
- `config/index.md`
- `config/projects.yaml`
- `assets/style.css`
- `pulses/seeds/*.txt`
- `src/*.py`

## GitHub Pages Configuration
- **Source**: `main` branch, root `/`
- **Custom domain**: `lexemancy.com`
- **HTTPS**: Enforced
- **Build type**: Legacy (not Actions)

---
