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
    """Load LLM configuration from .dev/.env or environment variables."""
    # Try to find .dev/.env
    env_path = find_workspace_env()
    if env_path:
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path, override=True)  # override=True to prioritize .env over existing env vars
            print(f"📁 Loaded config from: {env_path}")
        except ImportError:
            # dotenv not available, rely on environment variables
            print("⚠️ python-dotenv not available, using environment variables only")
        except Exception as e:
            print(f"⚠️ Failed to load .env from {env_path}: {e}")
    else:
        print("⚠️ No .dev/.env file found, using defaults and environment variables")
    
    provider = os.getenv("LLM_PROVIDER", "lmstudio").lower()
    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("LMSTUDIO_API_KEY", "")
    base_url = os.getenv("LLM_BASE_URL", "")
    
    # Resolve default URLs if not provided
    if not base_url:
        defaults = {
            "openrouter": "https://openrouter.ai/api/v1",
            "lmstudio": "http://localhost:1234/v1",
            "pollinations": "https://text.pollinations.ai/openai",
        }
        base_url = defaults.get(provider, "")
    
    model = os.getenv("LLM_MODEL", "gpt-oss-20b-heretic" if provider == "lmstudio" else ("openrouter/anthropic/claude-3.5-sonnet" if provider == "openrouter" else "gpt-oss-20b-heretic"))
    
    print(f"🔧 LLM Config: provider={provider}, base_url={base_url}, model={model}")
    
    return {
        "provider": provider,
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
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


def generate_with_llm(field_name: str, seed_examples: list[str], cache_examples: list[str], config: dict) -> Optional[str]:
    """
    Generate new content using LLM with seed and cache examples.
    Uses HTTP requests to OpenAI-compatible endpoint.
    """
    if not seed_examples and not cache_examples:
        return None
    
    # Sample 3 from seed + up to 3 from cache
    examples = sample_seeds(seed_examples, cache_examples, seed_count=3, cache_count=3)
    
    # Build field-specific prompts
    prompts = {
        "statuses": """You are generating mystical status messages for a recursive pulse log. Generate a new status message that matches the aesthetic and style of these examples.

Examples:
{examples}

Generate a single new status message (1-2 sentences max) that maintains the mystical, poetic, technical aesthetic. Be creative but coherent.""",

        "quotes": """You are generating mystical antenna quotes for a recursive pulse log. Generate a new quote that matches the aesthetic and style of these examples.

Examples:
{examples}

Generate a single new quote (1-2 sentences max) that maintains the mystical, poetic, technical aesthetic with references to language, symbols, recursion, and consciousness.""",

        "glyphs": """You are generating cryptoglyph descriptions for a recursive pulse log. Generate a new glyph description that matches the aesthetic and style of these examples.

Examples:
{examples}

Generate a single new glyph description (emoji sequence or symbolic text, keep it concise) that maintains the mystical aesthetic.""",

        "subjects": """You are generating subject identifiers for a recursive pulse log. Generate a new subject ID that matches the aesthetic and style of these examples.

Examples:
{examples}

Generate a single new subject identifier (concise, symbolic, mystical) that maintains the aesthetic.""",

        "echoes": """You are generating echo fragment classifications for a recursive pulse log. Generate a new echo classification that matches the aesthetic and style of these examples.

Examples:
{examples}

Generate a single new echo fragment classification (concise, poetic, symbolic) that maintains the aesthetic.""",

        "modes": """You are generating mode descriptions for a recursive pulse log. Generate a new mode description that matches the aesthetic and style of these examples.

Examples:
{examples}

Generate a single new mode description (concise, poetic, symbolic) that maintains the aesthetic.""",

        "end_quotes": """You are generating end quotes for a recursive pulse log. Generate a new end quote that matches the aesthetic and style of these examples.

Examples:
{examples}

Generate a single new end quote (1-2 sentences max, poetic, mystical) that maintains the aesthetic."""
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
        "temperature": 0.8,  # Creative but coherent
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


def generate_pulse_field(field_name: str, fallback_to_random: bool = True, config: dict = None) -> Optional[str]:
    """
    Generate a new pulse field value using LLM.
    Falls back to random seed selection if LLM unavailable.
    """
    seed_examples, cache_examples = load_seeds(field_name)
    if not seed_examples and not cache_examples:
        return None
    
    # Use provided config or load fresh
    if config is None:
        config = load_llm_config()
    
    # LMStudio doesn't require API key, so only check base_url
    if not config["base_url"]:
        if fallback_to_random:
            # Fallback to random from combined pool
            all_examples = seed_examples + cache_examples
            return random.choice(all_examples) if all_examples else None
        return None
    
    # For LMStudio, API key is optional
    if config["provider"] == "lmstudio" and not config["api_key"]:
        config["api_key"] = ""  # LMStudio doesn't require auth
    
    generated = generate_with_llm(field_name, seed_examples, cache_examples, config)
    
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
    # Load config once
    config = load_llm_config()
    
    results = {}
    
    for seed_file, field_key in FIELD_MAPPINGS.items():
        print(f"Generating {field_key}...")
        value = generate_pulse_field(seed_file, fallback_to_random=True, config=config)
        results[field_key] = value
        if value:
            print(f"  ✓ {value[:60]}...")
        else:
            print(f"  ⚠️ Failed to generate {field_key}")
    
    return results


if __name__ == "__main__":
    # Test generation
    print("🌀 Testing pulse generation...\n")
    fields = generate_all_pulse_fields()
    print("\n✅ Generation complete!")
    print("\nGenerated fields:")
    for key, value in fields.items():
        print(f"  {key}: {value}")
