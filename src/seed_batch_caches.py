import os
import random
from pathlib import Path


def lines_from_env_or_file(env_var: str, file_var: str, default_path: Path, fallback: list[str]) -> list[str]:
    if env_var in os.environ:
        return [ln.strip() for ln in os.environ[env_var].splitlines() if ln.strip()]
    path = Path(os.environ.get(file_var, default_path))
    try:
        with path.open(encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return fallback


def seed_cache(pool, cache_path, batch_size=5):
    pool = list({v for v in pool if v})
    if not pool:
        print(f"No values found to seed {cache_path.name}")
        return
    seed = random.sample(pool, min(batch_size, len(pool)))
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text("\n".join(seed) + "\n", encoding="utf-8")
    print(f"Seeded {cache_path} with: {seed}")


# --- FIELD CONFIGURATION (Update as needed) ---
REPO_ROOT = Path(__file__).resolve().parents[1]

fields = [
    # (env_var, file_var, default_path, fallback, cache_path, batch_size)
    (
        "STATUSES",
        "STATUS_FILE",
        REPO_ROOT / "pulses" / "statuses.txt",
        ["⚠️ status file missing"],
        REPO_ROOT / "pulses" / "status_cache.txt",
        5,
    ),
    (
        "ANTENNA_QUOTES",
        "QUOTE_FILE",
        REPO_ROOT / "pulses" / "antenna_quotes.txt",
        ["⚠️ quote file missing"],
        REPO_ROOT / "pulses" / "quote_cache.txt",
        5,
    ),
    (
        "GLYPH_BRAIDS",
        "GLYPH_FILE",
        REPO_ROOT / "pulses" / "glyphbraids.txt",
        ["⚠️ glyph file missing"],
        REPO_ROOT / "pulses" / "glyph_cache.txt",
        5,
    ),
    (
        "SUBJECT_IDS",
        "SUBJECT_FILE",
        REPO_ROOT / "pulses" / "subject-ids.txt",
        ["⚠️ subject file missing"],
        REPO_ROOT / "pulses" / "subject_cache.txt",
        5,
    ),
    (
        "ECHO_FRAGMENTS",
        "ECHO_FILE",
        REPO_ROOT / "pulses" / "echo_fragments.txt",
        ["⚠️ echo file missing"],
        REPO_ROOT / "pulses" / "echo_cache.txt",
        5,
    ),
    (
        "MODES",
        "MODE_FILE",
        REPO_ROOT / "pulses" / "modes.txt",
        ["⚠️ mode file missing"],
        REPO_ROOT / "pulses" / "mode_cache.txt",
        5,
    ),
    (
        "END_QUOTES",
        "END_QUOTE_FILE",
        REPO_ROOT / "pulses" / "end-quotes.txt",
        ["⚠️ end quote file missing"],
        REPO_ROOT / "pulses" / "end_quote_cache.txt",
        5,
    ),
]

for env_var, file_var, default_path, fallback, cache_path, batch_size in fields:
    pool = lines_from_env_or_file(env_var, file_var, default_path, fallback)
    if not cache_path.exists() or not cache_path.read_text(encoding="utf-8").strip():
        seed_cache(pool, cache_path, batch_size)
    else:
        print(f"Cache {cache_path} already exists, skipping.")
