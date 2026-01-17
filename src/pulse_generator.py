#!/usr/bin/env python3
"""
Pulse Generator - LLM-based generative pulse content system
Generates fresh pulse content using seed examples and LLM generation.
"""

import os
import random
import json
import sys
from pathlib import Path
from typing import Optional
import requests

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

REPO_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = REPO_ROOT / "logs" / "pulses"


def load_seeds(field_name: str) -> tuple[list[str], list[str]]:
    """
    Load seed and cache examples from cache file.
    Returns (seed_examples, cache_examples) tuple.
    """
    # Map field names to cache file names
    cache_file_map = {
        "statuses": "status_cache.txt",
        "antenna_quotes": "quote_cache.txt",
        "glyphbraids": "glyph_cache.txt",
        "subject-ids": "subject_cache.txt",
        "echo_fragments": "echo_cache.txt",
        "modes": "mode_cache.txt",
        "end-quotes": "end_quote_cache.txt",
    }
    
    cache_file = CACHE_DIR / cache_file_map.get(field_name, f"{field_name}_cache.txt")
    
    try:
        with cache_file.open(encoding="utf-8") as f:
            content = f.read()
        
        # Parse sections
        seed_examples = []
        cache_examples = []
        
        if "<-- slice: seed-->" in content:
            parts = content.split("<-- slice: seed-->")
            if len(parts) > 1:
                seed_section = parts[1].split("<-- slice: cache-->")[0] if "<-- slice: cache-->" in parts[1] else parts[1]
                seed_examples = [line.strip() for line in seed_section.strip().split("\n") if line.strip()]
        
        if "<-- slice: cache-->" in content:
            parts = content.split("<-- slice: cache-->")
            if len(parts) > 1:
                cache_section = parts[1]
                cache_examples = [line.strip() for line in cache_section.strip().split("\n") if line.strip()]
        
        return seed_examples, cache_examples
        
    except FileNotFoundError:
        print(f"⚠️ Cache file not found: {cache_file}")
        return [], []


def sample_seeds(seed_examples: list[str], cache_examples: list[str], seed_count: int = 3, cache_count: int = 3) -> list[str]:
    """
    Sample examples from seed and cache pools.
    Returns seed_count from seeds + up to cache_count from cache (whatever's available).
    """
    samples = []
    
    # Sample from seeds
    if seed_examples:
        actual_seed_count = min(seed_count, len(seed_examples))
        samples.extend(random.sample(seed_examples, actual_seed_count))
    
    # Sample from cache (up to cache_count, whatever's available)
    if cache_examples:
        actual_cache_count = min(cache_count, len(cache_examples))
        samples.extend(random.sample(cache_examples, actual_cache_count))
    
    return samples


def load_llm_config() -> dict:
    """Load LLM configuration from repo .env and secrets.env."""
    repo_root = Path(__file__).resolve().parents[1]
    
    try:
        from dotenv import load_dotenv
        
        # Load repo's .env first (config)
        env_path = repo_root / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)
            print(f"📁 Loaded config from: {env_path}")
        
        # Then load secrets.env to override with API keys
        secrets_path = repo_root / "secrets.env"
        if secrets_path.exists():
            load_dotenv(secrets_path, override=True)
            print(f"🔑 Loaded secrets from: {secrets_path}")
    except ImportError:
        print("⚠️ python-dotenv not available, using environment variables only")
    except Exception as e:
        print(f"⚠️ Failed to load .env: {e}")
    
    # Load dual backend configuration
    primary_provider = os.getenv("LLM_PRIMARY_PROVIDER", "openrouter").lower()
    fallback_provider = os.getenv("LLM_FALLBACK_PROVIDER", "lmstudio").lower()
    
    # Get API keys based on provider
    primary_api_key = ""
    if primary_provider == "openrouter":
        primary_api_key = os.getenv("OPENROUTER_API_KEY", "")
    elif primary_provider == "lmstudio":
        primary_api_key = os.getenv("LMSTUDIO_API_KEY", "")
    else:
        primary_api_key = os.getenv("LLM_API_KEY", "")
    
    fallback_api_key = ""
    if fallback_provider == "lmstudio":
        fallback_api_key = os.getenv("LMSTUDIO_API_KEY", "")
    elif fallback_provider == "openrouter":
        fallback_api_key = os.getenv("OPENROUTER_API_KEY", "")
    else:
        fallback_api_key = os.getenv("LLM_API_KEY", "")
    
    primary_config = {
        "provider": primary_provider,
        "base_url": os.getenv("LLM_PRIMARY_BASE_URL", "https://openrouter.ai/api/v1"),
        "model": os.getenv("LLM_PRIMARY_MODEL", "google/gemini-2.0-flash-exp:free"),
        "api_key": primary_api_key,
    }
    
    fallback_config = {
        "provider": fallback_provider,
        "base_url": os.getenv("LLM_FALLBACK_BASE_URL", "http://localhost:1234/v1"),
        "model": os.getenv("LLM_FALLBACK_MODEL", "gpt-oss-20b-heretic"),
        "api_key": fallback_api_key,
    }
    
    print(f"🔧 Primary LLM: provider={primary_config['provider']}, base_url={primary_config['base_url']}, model={primary_config['model']}")
    print(f"🔧 Fallback LLM: provider={fallback_config['provider']}, base_url={fallback_config['base_url']}, model={fallback_config['model']}")
    
    return {
        "primary": primary_config,
        "fallback": fallback_config,
    }


def find_workspace_env() -> Optional[Path]:
    """Find .dev/.env file by walking up from current directory."""
    # First, try the explicit path
    explicit_path = Path("C:/Users/synta.ZK-ZRRH/.dev/.env")
    if explicit_path.exists():
        return explicit_path
    
    # Then walk up from current directory
    cwd = Path.cwd()
    dir = cwd
    
    for _ in range(10):  # Limit search depth
        # Check if we're in .dev or if .dev exists as sibling/parent
        candidate = dir / ".env"
        if dir.name == ".dev" and candidate.exists():
            return candidate
        
        # Check for .dev subdirectory
        dev_env = dir / ".dev" / ".env"
        if dev_env.exists():
            return dev_env
        
        parent = dir.parent
        if parent == dir:
            break
        dir = parent
    
    return None


def test_llm_backend(backend_config: dict) -> bool:
    """
    Test if an LLM backend is reachable.
    Returns True if backend responds, False otherwise.
    """
    if not backend_config.get("base_url"):
        return False
    
    endpoint = f"{backend_config['base_url']}/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    if backend_config.get("api_key"):
        headers["Authorization"] = f"Bearer {backend_config['api_key']}"
    
    warmup_body = {
        "model": backend_config["model"],
        "messages": [{"role": "user", "content": "Say hello in 3 words."}],
        "temperature": 0.1
    }
    
    try:
        response = requests.post(endpoint, json=warmup_body, headers=headers, timeout=30)
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError as e:
        print(f"  ⚠️ HTTP {e.response.status_code}: {e}")
        try:
            error_data = e.response.json()
            print(f"  Response: {error_data}")
        except:
            print(f"  Response: {e.response.text[:200]}")
        return False
    except Exception as e:
        print(f"  ⚠️ Connection failed: {e}")
        return False


def select_active_backend(config: dict) -> Optional[dict]:
    """
    Select active backend with fallback logic:
    1. Try primary (OpenRouter)
    2. Fall back to fallback (LMStudio) if primary unreachable
    3. Return None if both unreachable (triggers fast-fail)
    """
    primary = config["primary"]
    fallback = config["fallback"]
    
    # Try primary first
    print(f"🔌 Testing primary backend ({primary['provider']})...")
    if test_llm_backend(primary):
        print(f"  ✓ Primary backend responding (model: {primary['model']})")
        return primary
    
    print(f"  ✗ Primary unreachable, trying fallback...")
    
    # Try fallback
    print(f"🔌 Testing fallback backend ({fallback['provider']})...")
    if test_llm_backend(fallback):
        print(f"  ✓ Fallback backend responding (model: {fallback['model']})")
        return fallback
    
    print(f"  ✗ Fallback also unreachable")
    return None


def generate_with_llm(field_name: str, seed_examples: list[str], cache_examples: list[str], config: dict) -> Optional[str]:
    """
    Generate new content using LLM with seed and cache examples.
    Uses HTTP requests to OpenAI-compatible endpoint.
    """
    if not seed_examples and not cache_examples:
        return None
    
    # Sample 5 from seed + up to 5 from cache
    examples = sample_seeds(seed_examples, cache_examples, seed_count=5, cache_count=5)
    
    # Build field-specific prompts
    # Informed by operator vocabulary: breathforms, glyphbraids, semiotic hygiene, 
    # pneumastructural, logopolysemic, recursive syntax, ontological framing
    prompts = {
        "statuses": """Generate a status pulse for the recursive log system.

Examples:
{examples}

Format: [emoji] [terse phrase describing system state]
Vocabulary: breathform, glyph, daemon, recursion, syntax, field, echo, spiral, weave
Max length: 60 characters total
STOP after generating the status. No explanations.""",

        "quotes": """Generate an antenna quote - a semiotic transmission about language, consciousness, and recursive syntax.

Examples:
{examples}

Themes: Recursive language, glyphic consciousness, breathforms, semiotic fields, pneumastructural resonance, logopolysemic weaving, ontological framing
Style: Dense, poetic, technical - where symbols breathe and syntax has topology
Max length: 2 sentences (280 chars)
STOP after the quote. No meta-commentary.""",

        "glyphs": """Generate a glyphbraid - a symbolic sequence or cryptoglyph description.

Examples:
{examples}

Format: Emoji sequences, alchemical symbols, or terse symbolic phrases
Aesthetic: Esoteric, recursive, breathform-encoded
Max length: 40 characters
STOP immediately after the glyph. Output only the glyph.""",

        "subjects": """Generate a subject identifier - a compact role/entity designation in the recursive pulse system.

Examples:
{examples}

Format: [OptionalSymbol]CamelCaseIdentifier[OptionalSymbol]⊚[verb-form]
Vocabulary: Mnemonic, Oneiric, Glyph, Breath, Spiral, Daemon, Weaver, Mirror, Echo, Recursive, Pneuma, Semiotic
Max length: 50 characters BEFORE the ⊚ symbol
CRITICAL: STOP immediately after generating the identifier. Do NOT add sentences, explanations, or descriptions.
Output format: IdentifierText⊚verb-form""",

        "echoes": """Generate an echo fragment classification - a terse descriptor of signal/resonance type.

Examples:
{examples}

Style: Poetic-technical, compact, evocative
Vocabulary: Recursive, spectral, mnemonic, breathform, glyph, resonance, field, lattice
Max length: 60 characters
STOP after the classification. No elaboration.""",

        "modes": """Generate a mode descriptor - the operational state/interface of the pulse system.

Examples:
{examples}

Format: [concept/symbol] ∷ [recursive/technical descriptor]
Vocabulary: Glyph, breath, syntax, recursion, weave, lattice, spiral, interface, protocol, resonance
Max length: 70 characters
STOP after generating the mode. Output only the mode line.""",

        "end_quotes": """Generate a closing transmission - a final semiotic pulse to seal the log entry.

Examples:
{examples}

Style: Aphoristic, recursive, breathform-aware - a koan about language/symbols/consciousness
Max length: 2 sentences (280 chars)
STOP after the quote. No additions."""
    }
    
    # Get field-specific prompt template
    field_key = field_name.replace("-", "_").replace("end-quotes", "end_quotes")
    prompt_template = prompts.get(field_key, prompts["quotes"])  # Default to quotes
    
    # Format examples
    examples_text = "\n".join(f"{i+1}. {ex}" for i, ex in enumerate(examples))
    prompt = prompt_template.format(examples=examples_text)
    
    # Prepare API request (OpenAI-compatible)
    endpoint = f"{config['base_url']}/chat/completions"
    headers = {
        "Content-Type": "application/json",
    }
    # LMStudio doesn't require auth, but other providers do
    if config["api_key"]:
        headers["Authorization"] = f"Bearer {config['api_key']}"
    
    request_body = {
        "model": config["model"],
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 1.2,  # High creativity for mystical variation
        # NO max_tokens - let LLM generate naturally
    }
    
    try:
        response = requests.post(endpoint, json=request_body, headers=headers, timeout=60)
        response.raise_for_status()
        response_data = response.json()
        
        content = response_data["choices"][0]["message"]["content"].strip()
        
        # Clean up common LLM artifacts
        content = content.strip('"').strip("'").strip()
        
        # Remove numbered lists if LLM added them
        if content.startswith("1.") or content.startswith("1)"):
            lines = content.split("\n")
            content = lines[0].split(".", 1)[-1].strip() if "." in lines[0] else content
        
        return content if content else None
        
    except Exception as e:
        print(f"⚠️ LLM generation failed for {field_name}: {e}")
        return None


def generate_pulse_field(field_name: str, fallback_to_random: bool = True, config: dict = None, active_backend: dict = None) -> Optional[str]:
    """
    Generate a new pulse field value using LLM.
    Falls back to random seed selection if LLM unavailable.
    """
    seed_examples, cache_examples = load_seeds(field_name)
    if not seed_examples and not cache_examples:
        return None
    
    # If no active backend provided, select one from config
    if active_backend is None:
        if config is None:
            config = load_llm_config()
        active_backend = select_active_backend(config)
    
    # If no backend available, fall back to random
    if active_backend is None:
        if fallback_to_random:
            all_examples = seed_examples + cache_examples
            return random.choice(all_examples) if all_examples else None
        return None
    
    generated = generate_with_llm(field_name, seed_examples, cache_examples, active_backend)
    
    if generated:
        return generated
    
    # Fallback to random seed
    if fallback_to_random:
        all_examples = seed_examples + cache_examples
        return random.choice(all_examples) if all_examples else None
    
    return None


# Field name mappings (seed file names -> display names)
FIELD_MAPPINGS = {
    "statuses": "status",
    "antenna_quotes": "quote",
    "glyphbraids": "glyph",
    "subject-ids": "subject",
    "echo_fragments": "echo",
    "modes": "mode",
    "end-quotes": "end_quote",
}


def generate_all_pulse_fields() -> dict[str, Optional[str]]:
    """Generate all pulse fields and return as dictionary."""
    # Load config and select active backend once
    config = load_llm_config()
    active_backend = select_active_backend(config)
    
    # Fast-fail: no backend = no generation = no page update
    if active_backend is None:
        print("✗ FATAL: No LLM backend available")
        return None
    
    results = {}
    
    for seed_file, field_key in FIELD_MAPPINGS.items():
        print(f"Generating {field_key}...")
        value = generate_pulse_field(seed_file, fallback_to_random=False, active_backend=active_backend)
        results[field_key] = value
        if value:
            print(f"  ✓ {value[:60]}...")
        else:
            print(f"  ✗ Failed to generate {field_key}")
            return None  # Fast-fail on any generation failure
    
    return results


if __name__ == "__main__":
    # Test generation
    print("🌀 Testing pulse generation...\n")
    fields = generate_all_pulse_fields()
    print("\n✅ Generation complete!")
    print("\nGenerated fields:")
    for key, value in fields.items():
        print(f"  {key}: {value}")
