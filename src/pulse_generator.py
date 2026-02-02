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
TEMPLATES_DIR = REPO_ROOT / "templates" / "prompts"


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


def generate_structural_batch(backend_config: dict) -> Optional[dict]:
    """
    Generate all 5 structural fields (status, subject, mode, glyph, echo) in a single batch call.
    Uses the pulse-structural-batch.md template with full operator context.
    """
    print("🌀 Generating structural batch...")
    
    # Load template
    template_path = TEMPLATES_DIR / "pulse-structural-batch.md"
    try:
        with template_path.open(encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        print(f"  ⚠️ Template not found: {template_path}")
        return None
    
    # Load examples from each cache
    status_seed, status_cache = load_seeds("statuses")
    subject_seed, subject_cache = load_seeds("subject-ids")
    mode_seed, mode_cache = load_seeds("modes")
    glyph_seed, glyph_cache = load_seeds("glyphbraids")
    echo_seed, echo_cache = load_seeds("echo_fragments")
    
    # Sample 3 from each
    status_examples = "\n".join(sample_seeds(status_seed, status_cache, 3, 3))
    subject_examples = "\n".join(sample_seeds(subject_seed, subject_cache, 3, 3))
    mode_examples = "\n".join(sample_seeds(mode_seed, mode_cache, 3, 3))
    glyph_examples = "\n".join(sample_seeds(glyph_seed, glyph_cache, 3, 3))
    echo_examples = "\n".join(sample_seeds(echo_seed, echo_cache, 3, 3))
    
    # Format template
    prompt = template.replace("{status_examples}", status_examples)
    prompt = prompt.replace("{subject_examples}", subject_examples)
    prompt = prompt.replace("{mode_examples}", mode_examples)
    prompt = prompt.replace("{glyph_examples}", glyph_examples)
    prompt = prompt.replace("{echo_examples}", echo_examples)
    
    # Remove example_json placeholders (not implemented yet)
    prompt = prompt.replace("{example_json_1}", "")
    prompt = prompt.replace("{example_json_2}", "")
    prompt = prompt.replace("{example_json_3}", "")
    
    # Call LLM
    endpoint = f"{backend_config['base_url']}/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    if backend_config.get("api_key"):
        headers["Authorization"] = f"Bearer {backend_config['api_key']}"
    
    request_body = {
        "model": backend_config["model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 1.2,
    }
    
    try:
        response = requests.post(endpoint, json=request_body, headers=headers, timeout=120)
        response.raise_for_status()
        response_data = response.json()
        
        content = response_data["choices"][0]["message"]["content"].strip()
        
        # Try to parse JSON
        # Remove markdown code fences if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        result = json.loads(content)
        print(f"  ✓ Batch generated: {len(result)} fields")
        return result
        
    except Exception as e:
        print(f"  ✗ Batch generation failed: {e}")
        return None


def generate_quote_with_template(backend_config: dict, quote_type: str) -> Optional[str]:
    """
    Generate antenna or end quote using template-based prompts.
    
    Args:
        backend_config: LLM backend configuration
        quote_type: "antenna" or "end"
    """
    print(f"🌀 Generating {quote_type} quote...")
    
    # Load template
    if quote_type == "antenna":
        template_path = TEMPLATES_DIR / "pulse-antenna-quote.md"
        cache_field = "antenna_quotes"
    else:
        template_path = TEMPLATES_DIR / "pulse-end-quote.md"
        cache_field = "end-quotes"
    
    try:
        with template_path.open(encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        print(f"  ⚠️ Template not found: {template_path}")
        return None
    
    # Load examples
    seed_examples, cache_examples = load_seeds(cache_field)
    
    # Sample 3 examples
    sampled = sample_seeds(seed_examples, cache_examples, 3, 3)
    examples_text = "\n\n".join(sampled)
    
    # Format template
    if quote_type == "antenna":
        prompt = template.replace("{antenna_quote_examples}", examples_text)
    else:
        prompt = template.replace("{end_quote_examples}", examples_text)
    
    # Call LLM
    endpoint = f"{backend_config['base_url']}/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    if backend_config.get("api_key"):
        headers["Authorization"] = f"Bearer {backend_config['api_key']}"
    
    request_body = {
        "model": backend_config["model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 1.2,
    }
    
    try:
        response = requests.post(endpoint, json=request_body, headers=headers, timeout=120)
        response.raise_for_status()
        response_data = response.json()
        
        content = response_data["choices"][0]["message"]["content"].strip()
        content = content.strip('"').strip("'").strip()
        
        print(f"  ✓ Generated {quote_type} quote ({len(content)} chars)")
        return content
        
    except Exception as e:
        print(f"  ✗ Quote generation failed: {e}")
        return None


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
    
    # Get primary backend selection
    primary_backend = os.getenv("LLM_PRIMARY_BACKEND", "openrouter").lower()
    
    # Backend configurations - dynamically build from env vars
    backends = {}
    
    # Scan for all backend configurations
    for key in os.environ:
        if key.endswith("_PROVIDER"):
            backend_name = key.replace("LLM_", "").replace("_PROVIDER", "").lower()
            provider = os.getenv(key, "")
            base_url = os.getenv(f"LLM_{backend_name.upper()}_BASE_URL", "")
            model = os.getenv(f"LLM_{backend_name.upper()}_MODEL", "")
            
            # Get API key based on provider type
            api_key = ""
            if "openrouter" in provider:
                api_key = os.getenv("OPENROUTER_API_KEY", "")
            elif "lmstudio" in provider:
                api_key = os.getenv("LMSTUDIO_API_KEY", "")
            elif "anthropic" in provider:
                api_key = os.getenv("ANTHROPIC_API_KEY", "")
            
            backends[backend_name] = {
                "provider": provider,
                "base_url": base_url,
                "model": model,
                "api_key": api_key,
            }
    
    # Fallback to hardcoded defaults if no backends found
    if not backends:
        backends = {
            "openrouter": {
                "provider": "openrouter",
                "base_url": "https://openrouter.ai/api/v1",
                "model": "deepseek/deepseek-v3.2",
                "api_key": os.getenv("OPENROUTER_API_KEY", ""),
            },
            "lmstudio": {
                "provider": "lmstudio",
                "base_url": "http://localhost:1234/v1",
                "model": "gpt-oss-20b-heretic",
                "api_key": os.getenv("LMSTUDIO_API_KEY", ""),
            },
        }
    
    # Select primary (or first available as fallback)
    primary_config = backends.get(primary_backend)
    if not primary_config:
        print(f"⚠️ Primary backend '{primary_backend}' not found, using first available")
        primary_config = list(backends.values())[0]
    
    # Build fallback list (all backends except primary, in order)
    fallback_configs = [config for name, config in backends.items() if name != primary_backend]
    
    print(f"🔧 Primary LLM: provider={primary_config['provider']}, base_url={primary_config['base_url']}, model={primary_config['model']}")
    if fallback_configs:
        print(f"🔧 Fallback LLMs: {len(fallback_configs)} configured")
    
    return {
        "primary": primary_config,
        "fallback": fallback_configs[0] if fallback_configs else primary_config,
        "all_fallbacks": fallback_configs,
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


def append_to_cache(field_name: str, value: str) -> None:
    """Append generated value to cache file for recursive feedback loop."""
    cache_file_map = {
        "status": "status_cache.txt",
        "quote": "quote_cache.txt",
        "glyph": "glyph_cache.txt",
        "subject": "subject_cache.txt",
        "echo": "echo_cache.txt",
        "mode": "mode_cache.txt",
        "end_quote": "end_quote_cache.txt",
    }
    
    cache_file = CACHE_DIR / cache_file_map.get(field_name, f"{field_name}_cache.txt")
    
    try:
        with cache_file.open("r", encoding="utf-8") as f:
            content = f.read()
        
        # Append to cache section (after <-- slice: cache-->)
        if "<-- slice: cache-->" in content:
            # Append new value after cache marker
            with cache_file.open("a", encoding="utf-8") as f:
                f.write(f"\n{value}")
            print(f"  📝 Cached {field_name}")
        else:
            print(f"  ⚠️ No cache section in {cache_file.name}")
    except FileNotFoundError:
        print(f"  ⚠️ Cache file not found: {cache_file}")
    except Exception as e:
        print(f"  ⚠️ Failed to cache {field_name}: {e}")


def generate_all_pulse_fields() -> dict[str, Optional[str]]:
    """Generate all pulse fields using 3-phase hybrid architecture."""
    # Load config and select active backend once
    config = load_llm_config()
    active_backend = select_active_backend(config)
    
    # Fast-fail: no backend = no generation = no page update
    if active_backend is None:
        print("✗ FATAL: No LLM backend available")
        return None
    
    results = {}
    
    # Phase 1: Structural Batch (status, subject, mode, glyph, echo)
    print("\n" + "=" * 60)
    print("PHASE 1: STRUCTURAL BATCH")
    print("=" * 60)
    
    batch_result = generate_structural_batch(active_backend)
    
    if batch_result:
        # Map batch results to field names
        results["status"] = batch_result.get("status")
        results["subject"] = batch_result.get("subject")
        results["mode"] = batch_result.get("mode")
        results["glyph"] = batch_result.get("glyph")
        results["echo"] = batch_result.get("echo")
        
        # Validate all fields present
        for field in ["status", "subject", "mode", "glyph", "echo"]:
            if not results.get(field):
                print(f"  ✗ Missing field: {field}")
                return None
        
        # Cache structural batch results for recursive feedback
        for field in ["status", "subject", "mode", "glyph", "echo"]:
            append_to_cache(field, results[field])
    else:
        print("  ✗ Structural batch failed")
        return None
    
    # Phase 2: Antenna Quote (future-aligned)
    print("\n" + "=" * 60)
    print("PHASE 2: ANTENNA QUOTE (Future-aligned)")
    print("=" * 60)
    
    antenna_quote = generate_quote_with_template(active_backend, "antenna")
    if antenna_quote:
        results["quote"] = antenna_quote
        append_to_cache("quote", antenna_quote)
    else:
        print("  ✗ Antenna quote failed")
        return None
    
    # Phase 3: End Quote (past-aligned)
    print("\n" + "=" * 60)
    print("PHASE 3: END QUOTE (Past-aligned)")
    print("=" * 60)
    
    end_quote = generate_quote_with_template(active_backend, "end")
    if end_quote:
        results["end_quote"] = end_quote
        append_to_cache("end_quote", end_quote)
    else:
        print("  ✗ End quote failed")
        return None
    
    print("\n" + "=" * 60)
    print("✓ ALL PHASES COMPLETE")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    # Test generation
    print("🌀 Testing pulse generation...\n")
    fields = generate_all_pulse_fields()
    print("\n✅ Generation complete!")
    print("\nGenerated fields:")
    for key, value in fields.items():
        print(f"  {key}: {value}")
