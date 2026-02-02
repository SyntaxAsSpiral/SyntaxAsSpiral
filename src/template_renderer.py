"""
Template renderer for Pulseframe.

Renders HTML templates with pulse data using simple {{variable}} substitution.
Supports multiple templates for different UI styles.
"""

import json
import re
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def load_template(template_name: str = "default") -> str:
    """Load a template file by name."""
    template_path = TEMPLATES_DIR / f"{template_name}.html"
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    return template_path.read_text(encoding="utf-8")


def render(template: str, data: dict) -> str:
    """
    Render a template with pulse data.

    Replaces {{variable}} placeholders with values from data dict.
    Missing keys are left as empty strings.
    """
    def replace_var(match):
        key = match.group(1)
        return str(data.get(key, ""))

    return re.sub(r"\{\{(\w+)\}\}", replace_var, template)


def inject(content: str, data: dict) -> str:
    """
    Inject values into marker regions while preserving markers.
    
    Pattern: <!--{{var}}-->...<!--/{{var}}--> (or <!--/...-->)
    Replaces content between markers with value from data dict.
    Markers are preserved so subsequent runs can re-inject fresh values.
    
    Also handles simple {{var}} placeholders (replaced, not preserved).
    """
    def replace_injection(match):
        key = match.group(1)
        value = str(data.get(key, ""))
        # Preserve the marker structure with fresh value
        return f"<!--{{{{{key}}}}}-->{value}<!--/{{{{{key}}}}}-->"
    
    # Injection markers: <!--{{varname}}-->content<!--/{{varname}}--> 
    # OR <!--{{varname}}-->content<!--/anything--> (for recovery from corruption)
    # The key is inside double braces within the opening comment
    result = re.sub(
        r"<!--\{\{(\w+)\}\}-->.*?<!--/[^>]*-->",
        replace_injection,
        content,
        flags=re.DOTALL
    )
    
    # Simple placeholders (replaced, not preserved) - for templates like default.html
    # Skip any that are inside comment markers (protected)
    def replace_var(match):
        key = match.group(1)
        start = match.start()
        # Check if inside a comment marker - look for "<!--" or "<!--/" before
        prefix5 = result[max(0, start-5):start]
        if "<!--" in prefix5:
            return match.group(0)  # Leave it alone - it's a marker
        return str(data.get(key, ""))
    
    result = re.sub(r"\{\{(\w+)\}\}", replace_var, result)
    
    return result


def render_template(template_name: str, data: dict) -> str:
    """Load and render a template by name."""
    template = load_template(template_name)
    return render(template, data)


def render_from_pulse_json(pulse_json_path: Path, template_name: str = "default") -> str:
    """Load pulse.json and render with specified template."""
    with pulse_json_path.open("r", encoding="utf-8") as f:
        pulse_data = json.load(f)
    return render_template(template_name, pulse_data)


# CLI support for standalone rendering
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python template_renderer.py <pulse.json> [template_name]")
        print("       template_name defaults to 'default'")
        sys.exit(1)

    pulse_path = Path(sys.argv[1])
    template_name = sys.argv[2] if len(sys.argv) > 2 else "default"

    html = render_from_pulse_json(pulse_path, template_name)
    print(html)
