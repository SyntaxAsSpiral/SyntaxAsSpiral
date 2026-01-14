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
SEEDS_DIR = REPO_ROOT / "pulses" / "seeds"


def load_seeds(field_name: str) -> list[str]:
    """Load all seed lines from a seed file."""
    seed_file = SEEDS_DIR / f"{field_name}.txt"
    try:
        with seed_file.open(encoding="utf-8") as f:
            seeds = [line.strip() for line in f if line.strip()]
        return seeds
    except FileNotFoundError:
        print(f"⚠️ Seed file not found: {seed_file}")
        return []


def sample_seeds(seeds: list[str], count: int = 5) -> list[str]:
    """Sample exactly N random seeds from the pool."""
    if not seeds:
        return []
    count = min(count, len(seeds))
    return random.sample(seeds, count)


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


def generate_with_llm(field_name: str, seeds: list[str], config: dict) -> Optional[str]:
    """
    Generate new content using LLM with seed examples.
    Uses HTTP requests to OpenAI-compatible endpoint.
    """
    if not seeds:
        return None
    
    # Sample exactly 5 random seeds
    examples = sample_seeds(seeds, 5)
    
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
    seeds = load_seeds(field_name)
    if not seeds:
        return None
    
    # Use provided config or load fresh
    if config is None:
        config = load_llm_config()
    
    # LMStudio doesn't require API key, so only check base_url
    if not config["base_url"]:
        if fallback_to_random:
            return random.choice(seeds)
        return None
    
    # For LMStudio, API key is optional
    if config["provider"] == "lmstudio" and not config["api_key"]:
        config["api_key"] = ""  # LMStudio doesn't require auth
    
    generated = generate_with_llm(field_name, seeds, config)
    
    if generated:
        return generated
    
    # Fallback to random seed
    if fallback_to_random:
        return random.choice(seeds)
    
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
