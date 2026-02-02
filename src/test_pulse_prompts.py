#!/usr/bin/env python3
"""
Test script for refined pulse prompts.
Tests batch generation, format compliance, and aesthetic quality.
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Optional
import requests

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

REPO_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = REPO_ROOT / "logs" / "pulses"
TEMPLATES_DIR = REPO_ROOT / "templates"


def load_llm_config() -> dict:
    """Load LLM configuration from .env files."""
    try:
        from dotenv import load_dotenv
        
        env_path = REPO_ROOT / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)
        
        secrets_path = REPO_ROOT / "secrets.env"
        if secrets_path.exists():
            load_dotenv(secrets_path, override=True)
    except ImportError:
        print("⚠️ python-dotenv not available")
    except Exception as e:
        print(f"⚠️ Failed to load .env: {e}")
    
    primary_provider = os.getenv("LLM_PRIMARY_PROVIDER", "lmstudio").lower()
    fallback_provider = os.getenv("LLM_FALLBACK_PROVIDER", "openrouter").lower()
    
    primary_api_key = ""
    if primary_provider == "openrouter":
        primary_api_key = os.getenv("OPENROUTER_API_KEY", "")
    elif primary_provider == "lmstudio":
        primary_api_key = os.getenv("LMSTUDIO_API_KEY", "")
    
    fallback_api_key = ""
    if fallback_provider == "lmstudio":
        fallback_api_key = os.getenv("LMSTUDIO_API_KEY", "")
    elif fallback_provider == "openrouter":
        fallback_api_key = os.getenv("OPENROUTER_API_KEY", "")
    
    primary_config = {
        "provider": primary_provider,
        "base_url": os.getenv("LLM_PRIMARY_BASE_URL", "http://localhost:1234/v1"),
        "model": os.getenv("LLM_PRIMARY_MODEL", "gpt-oss-20b-heretic"),
        "api_key": primary_api_key,
    }
    
    fallback_config = {
        "provider": fallback_provider,
        "base_url": os.getenv("LLM_FALLBACK_BASE_URL", "https://openrouter.ai/api/v1"),
        "model": os.getenv("LLM_FALLBACK_MODEL", "deepseek/deepseek-v3.2"),
        "api_key": fallback_api_key,
    }
    
    return {
        "primary": primary_config,
        "fallback": fallback_config,
    }


def test_backend(backend_config: dict) -> bool:
    """Test if backend is reachable."""
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
    except Exception as e:
        print(f"  ⚠️ {e}")
        return False


def select_active_backend(config: dict) -> Optional[dict]:
    """Select active backend with fallback logic."""
    primary = config["primary"]
    fallback = config["fallback"]
    
    print(f"🔌 Testing primary backend ({primary['provider']})...")
    if test_backend(primary):
        print(f"  ✓ Primary responding (model: {primary['model']})")
        return primary
    
    print(f"  ✗ Primary unreachable, trying fallback...")
    print(f"🔌 Testing fallback backend ({fallback['provider']})...")
    if test_backend(fallback):
        print(f"  ✓ Fallback responding (model: {fallback['model']})")
        return fallback
    
    print(f"  ✗ Fallback also unreachable")
    return None


def load_cache_examples(cache_file: Path) -> tuple[list[str], list[str]]:
    """Load seed and cache examples from cache file."""
    try:
        with cache_file.open(encoding="utf-8") as f:
            content = f.read()
        
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
        return [], []


def generate_structural_batch(backend_config: dict) -> Optional[dict]:
    """Generate all 5 structural fields in a single batch call."""
    print("\n🌀 Generating structural batch (status, subject, mode, glyph, echo)...")
    
    # Load template
    template_path = TEMPLATES_DIR / "pulse-structural-batch.md"
    with template_path.open(encoding="utf-8") as f:
        template = f.read()
    
    # Load examples from each cache
    status_seed, status_cache = load_cache_examples(CACHE_DIR / "status_cache.txt")
    subject_seed, subject_cache = load_cache_examples(CACHE_DIR / "subject_cache.txt")
    mode_seed, mode_cache = load_cache_examples(CACHE_DIR / "mode_cache.txt")
    glyph_seed, glyph_cache = load_cache_examples(CACHE_DIR / "glyph_cache.txt")
    echo_seed, echo_cache = load_cache_examples(CACHE_DIR / "echo_cache.txt")
    
    # Sample 3 from each
    import random
    status_examples = "\n".join(random.sample(status_seed + status_cache, min(3, len(status_seed + status_cache))))
    subject_examples = "\n".join(random.sample(subject_seed + subject_cache, min(3, len(subject_seed + subject_cache))))
    mode_examples = "\n".join(random.sample(mode_seed + mode_cache, min(3, len(mode_seed + mode_cache))))
    glyph_examples = "\n".join(random.sample(glyph_seed + glyph_cache, min(3, len(glyph_seed + glyph_cache))))
    echo_examples = "\n".join(random.sample(echo_seed + echo_cache, min(3, len(echo_seed + echo_cache))))
    
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
        return result
        
    except Exception as e:
        print(f"  ✗ Batch generation failed: {e}")
        return None


def generate_quote(backend_config: dict, quote_type: str) -> Optional[str]:
    """Generate antenna or end quote."""
    print(f"\n🌀 Generating {quote_type} quote...")
    
    # Load template
    if quote_type == "antenna":
        template_path = TEMPLATES_DIR / "pulse-antenna-quote.md"
        cache_file = CACHE_DIR / "quote_cache.txt"
    else:
        template_path = TEMPLATES_DIR / "pulse-end-quote.md"
        cache_file = CACHE_DIR / "end_quote_cache.txt"
    
    with template_path.open(encoding="utf-8") as f:
        template = f.read()
    
    # Load examples
    seed_examples, cache_examples = load_cache_examples(cache_file)
    
    # Sample 3 examples
    import random
    all_examples = seed_examples + cache_examples
    sampled = random.sample(all_examples, min(3, len(all_examples)))
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
        
        return content
        
    except Exception as e:
        print(f"  ✗ Quote generation failed: {e}")
        return None


def validate_format(field_name: str, value: str) -> dict:
    """Validate field format and length constraints."""
    issues = []
    
    if field_name == "status":
        if len(value) > 60:
            issues.append(f"Length {len(value)} exceeds 60 chars")
        if not re.match(r'^[^\s]+\s+', value):
            issues.append("Missing emoji at start")
    
    elif field_name == "subject":
        if "⊚" not in value:
            issues.append("Missing ⊚ separator")
        else:
            before_sep = value.split("⊚")[0]
            if len(before_sep) > 50:
                issues.append(f"Identifier length {len(before_sep)} exceeds 50 chars")
    
    elif field_name == "mode":
        if "∷" not in value:
            issues.append("Missing ∷ separator")
        if len(value) > 70:
            issues.append(f"Length {len(value)} exceeds 70 chars")
    
    elif field_name == "glyph":
        if "∵" not in value:
            issues.append("Missing ∵ separator")
        if len(value) > 40:
            issues.append(f"Length {len(value)} exceeds 40 chars")
    
    elif field_name == "echo":
        if "⇝" not in value:
            issues.append("Missing ⇝ prefix")
        if len(value) > 60:
            issues.append(f"Length {len(value)} exceeds 60 chars")
    
    elif field_name in ["antenna_quote", "end_quote"]:
        if len(value) > 280:
            issues.append(f"Length {len(value)} exceeds 280 chars")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "length": len(value)
    }


def check_aesthetic_quality(field_name: str, value: str) -> dict:
    """Check if output matches operator vocabulary and aesthetic."""
    operator_vocab = [
        "breathform", "glyphbraid", "semiotic", "pneumastructural", "logopolysemic",
        "recursive", "daemon", "spiral", "weave", "lattice", "resonance", "field",
        "echo", "mirror", "shimmer", "hyperstition", "wyrd", "geomythic", "primordial",
        "fossil", "substrate", "marrow", "ancestral", "numen", "becoming", "emergence"
    ]
    
    value_lower = value.lower()
    vocab_matches = [word for word in operator_vocab if word in value_lower]
    
    # Check for mystical-technical blend
    has_mystical = any(word in value_lower for word in ["glyph", "daemon", "breath", "wyrd", "numen", "echo"])
    has_technical = any(word in value_lower for word in ["syntax", "recursive", "lattice", "protocol", "interface", "code"])
    
    return {
        "vocab_matches": vocab_matches,
        "vocab_count": len(vocab_matches),
        "has_mystical": has_mystical,
        "has_technical": has_technical,
        "mystical_technical_blend": has_mystical and has_technical
    }


def run_test_suite():
    """Run comprehensive test suite for refined prompts."""
    print("=" * 80)
    print("PULSE PROMPT TEST SUITE")
    print("=" * 80)
    
    # Load config and select backend
    config = load_llm_config()
    backend = select_active_backend(config)
    
    if not backend:
        print("\n✗ FATAL: No LLM backend available")
        return
    
    print(f"\n✓ Using backend: {backend['provider']} ({backend['model']})")
    
    # Test 1: Structural Batch Generation
    print("\n" + "=" * 80)
    print("TEST 1: STRUCTURAL BATCH GENERATION")
    print("=" * 80)
    
    batch_result = generate_structural_batch(backend)
    
    if batch_result:
        print("\n✓ Batch generation successful!")
        print("\nGenerated fields:")
        for field, value in batch_result.items():
            print(f"\n  {field.upper()}:")
            print(f"    {value}")
            
            # Validate format
            validation = validate_format(field, value)
            print(f"    Format: {'✓ VALID' if validation['valid'] else '✗ INVALID'}")
            if validation['issues']:
                for issue in validation['issues']:
                    print(f"      - {issue}")
            print(f"    Length: {validation['length']} chars")
            
            # Check aesthetic
            aesthetic = check_aesthetic_quality(field, value)
            print(f"    Vocabulary matches: {aesthetic['vocab_count']} ({', '.join(aesthetic['vocab_matches'][:3])}...)")
            print(f"    Mystical-technical blend: {'✓' if aesthetic['mystical_technical_blend'] else '✗'}")
    else:
        print("\n✗ Batch generation failed")
    
    # Test 2: Antenna Quote Generation
    print("\n" + "=" * 80)
    print("TEST 2: ANTENNA QUOTE GENERATION (Future-aligned)")
    print("=" * 80)
    
    antenna_quote = generate_quote(backend, "antenna")
    
    if antenna_quote:
        print(f"\n✓ Generated: {antenna_quote}")
        
        validation = validate_format("antenna_quote", antenna_quote)
        print(f"\nFormat: {'✓ VALID' if validation['valid'] else '✗ INVALID'}")
        if validation['issues']:
            for issue in validation['issues']:
                print(f"  - {issue}")
        print(f"Length: {validation['length']} chars")
        
        aesthetic = check_aesthetic_quality("antenna_quote", antenna_quote)
        print(f"Vocabulary matches: {aesthetic['vocab_count']} ({', '.join(aesthetic['vocab_matches'])})")
        print(f"Mystical-technical blend: {'✓' if aesthetic['mystical_technical_blend'] else '✗'}")
    else:
        print("\n✗ Antenna quote generation failed")
    
    # Test 3: End Quote Generation
    print("\n" + "=" * 80)
    print("TEST 3: END QUOTE GENERATION (Past-aligned)")
    print("=" * 80)
    
    end_quote = generate_quote(backend, "end")
    
    if end_quote:
        print(f"\n✓ Generated: {end_quote}")
        
        validation = validate_format("end_quote", end_quote)
        print(f"\nFormat: {'✓ VALID' if validation['valid'] else '✗ INVALID'}")
        if validation['issues']:
            for issue in validation['issues']:
                print(f"  - {issue}")
        print(f"Length: {validation['length']} chars")
        
        aesthetic = check_aesthetic_quality("end_quote", end_quote)
        print(f"Vocabulary matches: {aesthetic['vocab_count']} ({', '.join(aesthetic['vocab_matches'])})")
        print(f"Mystical-technical blend: {'✓' if aesthetic['mystical_technical_blend'] else '✗'}")
    else:
        print("\n✗ End quote generation failed")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"\nBackend: {backend['provider']} ({backend['model']})")
    print(f"Structural batch: {'✓ SUCCESS' if batch_result else '✗ FAILED'}")
    print(f"Antenna quote: {'✓ SUCCESS' if antenna_quote else '✗ FAILED'}")
    print(f"End quote: {'✓ SUCCESS' if end_quote else '✗ FAILED'}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    run_test_suite()
