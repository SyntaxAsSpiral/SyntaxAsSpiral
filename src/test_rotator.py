import os
import subprocess
import sys
from pathlib import Path
import random


def test_rotator_creates_index(tmp_path):
    script_path = Path(__file__).resolve().parents[1] / "codex" / "github_status_rotator.py"
    statuses = tmp_path / "statuses.txt"
    statuses.write_text("alpha\nbeta\n", encoding="utf-8")
    quotes = tmp_path / "antenna_quotes.txt"
    quotes.write_text("echo\nnoecho\n", encoding="utf-8")
    glyphs = tmp_path / "glyphbraids.txt"
    glyphs.write_text("gamma\ndelta\n", encoding="utf-8")
    echoes = tmp_path / "echo_fragments.txt"
    echoes.write_text("sigil\nmirage\n", encoding="utf-8")
    modes = tmp_path / "modes.txt"
    modes.write_text('"m1"\n"m2"\n', encoding="utf-8")
    ends = tmp_path / "end-quotes.txt"
    ends.write_text("fin\nterm\n", encoding="utf-8")
    subjects = tmp_path / "subject-ids.txt"
    subjects.write_text("id1\nid2\n", encoding="utf-8")
    codex_dir = tmp_path / "codex"
    codex_dir.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["STATUS_FILE"] = str(statuses)
    env["QUOTE_FILE"] = str(quotes)
    env["GLYPH_FILE"] = str(glyphs)
    env["ECHO_FILE"] = str(echoes)
    env["MODE_FILE"] = str(modes)
    env["END_QUOTE_FILE"] = str(ends)
    env["SUBJECT_FILE"] = str(subjects)
    env["STATUS_CACHE_FILE"] = str(tmp_path / "status_cache.txt")
    env["QUOTE_CACHE_FILE"] = str(tmp_path / "quote_cache.txt")
    env["GLYPH_CACHE_FILE"] = str(tmp_path / "glyph_cache.txt")
    env["SUBJECT_CACHE_FILE"] = str(tmp_path / "subject_cache.txt")
    env["ECHO_CACHE_FILE"] = str(tmp_path / "echo_cache.txt")
    env["MODE_CACHE_FILE"] = str(tmp_path / "mode_cache.txt")
    env["END_QUOTE_CACHE_FILE"] = str(tmp_path / "end_quote_cache.txt")
    env["OUTPUT_DIR"] = str(tmp_path)
    subprocess.run([sys.executable, str(script_path)], cwd=tmp_path, check=True, env=env)
    assert not (tmp_path / "README.md").exists()
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "ChronoSig" in html
    assert any(s in html for s in ["alpha", "beta"])
    assert any(q in html for q in ["echo", "noecho"])
    assert any(g in html for g in ["gamma", "delta"])
    assert any(e in html for e in ["sigil", "mirage"])
    assert any(sub in html for sub in ["id1", "id2"])
    assert "recursive-log-banner.mp4" in html

def test_rotator_handles_missing_echo(tmp_path):
    script_path = Path(__file__).resolve().parents[1] / "codex" / "github_status_rotator.py"
    statuses = tmp_path / "statuses.txt"
    statuses.write_text("alpha\nbeta\n", encoding="utf-8")
    quotes = tmp_path / "antenna_quotes.txt"
    quotes.write_text("echo\nnoecho\n", encoding="utf-8")
    glyphs = tmp_path / "glyphbraids.txt"
    glyphs.write_text("gamma\ndelta\n", encoding="utf-8")
    modes = tmp_path / "modes.txt"
    modes.write_text('"a"\n"b"\n', encoding="utf-8")
    ends = tmp_path / "end-quotes.txt"
    ends.write_text("x\ny\n", encoding="utf-8")
    codex_dir = tmp_path / "codex"
    codex_dir.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["STATUS_FILE"] = str(statuses)
    env["QUOTE_FILE"] = str(quotes)
    env["GLYPH_FILE"] = str(glyphs)
    env["ECHO_FILE"] = str(tmp_path / "missing.txt")
    env["MODE_FILE"] = str(modes)
    env["END_QUOTE_FILE"] = str(ends)
    env["STATUS_CACHE_FILE"] = str(tmp_path / "status_cache.txt")
    env["QUOTE_CACHE_FILE"] = str(tmp_path / "quote_cache.txt")
    env["GLYPH_CACHE_FILE"] = str(tmp_path / "glyph_cache.txt")
    env["SUBJECT_CACHE_FILE"] = str(tmp_path / "subject_cache.txt")
    env["ECHO_CACHE_FILE"] = str(tmp_path / "echo_cache.txt")
    env["MODE_CACHE_FILE"] = str(tmp_path / "mode_cache.txt")
    env["END_QUOTE_CACHE_FILE"] = str(tmp_path / "end_quote_cache.txt")
    env["OUTPUT_DIR"] = str(tmp_path)
    subprocess.run([sys.executable, str(script_path)], cwd=tmp_path, check=True, env=env)
    assert not (tmp_path / "README.md").exists()
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "ChronoSig" in html
    assert "⚠️ echo file missing" in html


def test_rotator_handles_missing_status(tmp_path):
    script_path = Path(__file__).resolve().parents[1] / "codex" / "github_status_rotator.py"
    quotes = tmp_path / "antenna_quotes.txt"
    quotes.write_text("echo\nnoecho\n", encoding="utf-8")
    glyphs = tmp_path / "glyphbraids.txt"
    glyphs.write_text("gamma\ndelta\n", encoding="utf-8")
    echoes = tmp_path / "echo_fragments.txt"
    echoes.write_text("sigil\nmirage\n", encoding="utf-8")
    modes = tmp_path / "modes.txt"
    modes.write_text('"a"\n"b"\n', encoding="utf-8")
    ends = tmp_path / "end-quotes.txt"
    ends.write_text("x\ny\n", encoding="utf-8")
    subjects = tmp_path / "subject-ids.txt"
    subjects.write_text("id1\nid2\n", encoding="utf-8")
    codex_dir = tmp_path / "codex"
    codex_dir.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["STATUS_FILE"] = str(tmp_path / "missing.txt")
    env["QUOTE_FILE"] = str(quotes)
    env["GLYPH_FILE"] = str(glyphs)
    env["ECHO_FILE"] = str(echoes)
    env["MODE_FILE"] = str(modes)
    env["END_QUOTE_FILE"] = str(ends)
    env["SUBJECT_FILE"] = str(subjects)
    env["STATUS_CACHE_FILE"] = str(tmp_path / "status_cache.txt")
    env["QUOTE_CACHE_FILE"] = str(tmp_path / "quote_cache.txt")
    env["GLYPH_CACHE_FILE"] = str(tmp_path / "glyph_cache.txt")
    env["SUBJECT_CACHE_FILE"] = str(tmp_path / "subject_cache.txt")
    env["ECHO_CACHE_FILE"] = str(tmp_path / "echo_cache.txt")
    env["MODE_CACHE_FILE"] = str(tmp_path / "mode_cache.txt")
    env["END_QUOTE_CACHE_FILE"] = str(tmp_path / "end_quote_cache.txt")
    env["OUTPUT_DIR"] = str(tmp_path)
    subprocess.run([sys.executable, str(script_path)], cwd=tmp_path, check=True, env=env)
    assert not (tmp_path / "README.md").exists()
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "ChronoSig" in html
    assert "⚠️ status file missing" in html


def test_rotator_handles_missing_quote(tmp_path):
    script_path = Path(__file__).resolve().parents[1] / "codex" / "github_status_rotator.py"
    statuses = tmp_path / "statuses.txt"
    statuses.write_text("alpha\nbeta\n", encoding="utf-8")
    glyphs = tmp_path / "glyphbraids.txt"
    glyphs.write_text("gamma\ndelta\n", encoding="utf-8")
    echoes = tmp_path / "echo_fragments.txt"
    echoes.write_text("sigil\nmirage\n", encoding="utf-8")
    modes = tmp_path / "modes.txt"
    modes.write_text('"a"\n"b"\n', encoding="utf-8")
    ends = tmp_path / "end-quotes.txt"
    ends.write_text("x\ny\n", encoding="utf-8")
    subjects = tmp_path / "subject-ids.txt"
    subjects.write_text("id1\nid2\n", encoding="utf-8")
    codex_dir = tmp_path / "codex"
    codex_dir.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["STATUS_FILE"] = str(statuses)
    env["QUOTE_FILE"] = str(tmp_path / "missing.txt")
    env["GLYPH_FILE"] = str(glyphs)
    env["ECHO_FILE"] = str(echoes)
    env["MODE_FILE"] = str(modes)
    env["END_QUOTE_FILE"] = str(ends)
    env["SUBJECT_FILE"] = str(subjects)
    env["STATUS_CACHE_FILE"] = str(tmp_path / "status_cache.txt")
    env["QUOTE_CACHE_FILE"] = str(tmp_path / "quote_cache.txt")
    env["GLYPH_CACHE_FILE"] = str(tmp_path / "glyph_cache.txt")
    env["SUBJECT_CACHE_FILE"] = str(tmp_path / "subject_cache.txt")
    env["ECHO_CACHE_FILE"] = str(tmp_path / "echo_cache.txt")
    env["MODE_CACHE_FILE"] = str(tmp_path / "mode_cache.txt")
    env["END_QUOTE_CACHE_FILE"] = str(tmp_path / "end_quote_cache.txt")
    env["OUTPUT_DIR"] = str(tmp_path)
    subprocess.run([sys.executable, str(script_path)], cwd=tmp_path, check=True, env=env)
    assert not (tmp_path / "README.md").exists()
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "ChronoSig" in html
    assert "⚠️ quote file missing" in html


def test_rotator_handles_missing_glyph(tmp_path):
    script_path = Path(__file__).resolve().parents[1] / "codex" / "github_status_rotator.py"
    statuses = tmp_path / "statuses.txt"
    statuses.write_text("alpha\nbeta\n", encoding="utf-8")
    quotes = tmp_path / "antenna_quotes.txt"
    quotes.write_text("echo\nnoecho\n", encoding="utf-8")
    echoes = tmp_path / "echo_fragments.txt"
    echoes.write_text("sigil\nmirage\n", encoding="utf-8")
    subjects = tmp_path / "subject-ids.txt"
    subjects.write_text("id1\nid2\n", encoding="utf-8")
    modes = tmp_path / "modes.txt"
    modes.write_text('"a"\n"b"\n', encoding="utf-8")
    ends = tmp_path / "end-quotes.txt"
    ends.write_text("x\ny\n", encoding="utf-8")
    codex_dir = tmp_path / "codex"
    codex_dir.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["STATUS_FILE"] = str(statuses)
    env["QUOTE_FILE"] = str(quotes)
    env["GLYPH_FILE"] = str(tmp_path / "missing.txt")
    env["ECHO_FILE"] = str(echoes)
    env["MODE_FILE"] = str(modes)
    env["END_QUOTE_FILE"] = str(ends)
    env["SUBJECT_FILE"] = str(subjects)
    env["STATUS_CACHE_FILE"] = str(tmp_path / "status_cache.txt")
    env["QUOTE_CACHE_FILE"] = str(tmp_path / "quote_cache.txt")
    env["GLYPH_CACHE_FILE"] = str(tmp_path / "glyph_cache.txt")
    env["SUBJECT_CACHE_FILE"] = str(tmp_path / "subject_cache.txt")
    env["ECHO_CACHE_FILE"] = str(tmp_path / "echo_cache.txt")
    env["MODE_CACHE_FILE"] = str(tmp_path / "mode_cache.txt")
    env["END_QUOTE_CACHE_FILE"] = str(tmp_path / "end_quote_cache.txt")
    env["OUTPUT_DIR"] = str(tmp_path)
    subprocess.run([sys.executable, str(script_path)], cwd=tmp_path, check=True, env=env)
    assert not (tmp_path / "README.md").exists()
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "ChronoSig" in html
    assert "⚠️ glyph file missing" in html


def test_rotator_handles_missing_subject(tmp_path):
    script_path = Path(__file__).resolve().parents[1] / "codex" / "github_status_rotator.py"
    statuses = tmp_path / "statuses.txt"
    statuses.write_text("alpha\nbeta\n", encoding="utf-8")
    quotes = tmp_path / "antenna_quotes.txt"
    quotes.write_text("echo\nnoecho\n", encoding="utf-8")
    glyphs = tmp_path / "glyphbraids.txt"
    glyphs.write_text("gamma\ndelta\n", encoding="utf-8")
    echoes = tmp_path / "echo_fragments.txt"
    echoes.write_text("sigil\nmirage\n", encoding="utf-8")
    codex_dir = tmp_path / "codex"
    codex_dir.mkdir(exist_ok=True)
    modes = tmp_path / "modes.txt"
    modes.write_text('"a"\n"b"\n', encoding="utf-8")
    ends = tmp_path / "end-quotes.txt"
    ends.write_text("x\ny\n", encoding="utf-8")
    env = os.environ.copy()
    env["STATUS_FILE"] = str(statuses)
    env["QUOTE_FILE"] = str(quotes)
    env["GLYPH_FILE"] = str(glyphs)
    env["ECHO_FILE"] = str(echoes)
    env["MODE_FILE"] = str(modes)
    env["END_QUOTE_FILE"] = str(ends)
    env["SUBJECT_FILE"] = str(tmp_path / "missing.txt")
    env["STATUS_CACHE_FILE"] = str(tmp_path / "status_cache.txt")
    env["QUOTE_CACHE_FILE"] = str(tmp_path / "quote_cache.txt")
    env["GLYPH_CACHE_FILE"] = str(tmp_path / "glyph_cache.txt")
    env["SUBJECT_CACHE_FILE"] = str(tmp_path / "subject_cache.txt")
    env["ECHO_CACHE_FILE"] = str(tmp_path / "echo_cache.txt")
    env["MODE_CACHE_FILE"] = str(tmp_path / "mode_cache.txt")
    env["END_QUOTE_CACHE_FILE"] = str(tmp_path / "end_quote_cache.txt")
    env["OUTPUT_DIR"] = str(tmp_path)
    subprocess.run([sys.executable, str(script_path)], cwd=tmp_path, check=True, env=env)
    assert not (tmp_path / "README.md").exists()
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "ChronoSig" in html
    assert "⚠️ subject file missing" in html


def test_rotator_handles_missing_mode(tmp_path):
    script_path = Path(__file__).resolve().parents[1] / "codex" / "github_status_rotator.py"
    statuses = tmp_path / "statuses.txt"
    statuses.write_text("alpha\nbeta\n", encoding="utf-8")
    quotes = tmp_path / "antenna_quotes.txt"
    quotes.write_text("echo\nnoecho\n", encoding="utf-8")
    glyphs = tmp_path / "glyphbraids.txt"
    glyphs.write_text("gamma\ndelta\n", encoding="utf-8")
    echoes = tmp_path / "echo_fragments.txt"
    echoes.write_text("sigil\nmirage\n", encoding="utf-8")
    ends = tmp_path / "end-quotes.txt"
    ends.write_text("x\ny\n", encoding="utf-8")
    subjects = tmp_path / "subject-ids.txt"
    subjects.write_text("id1\nid2\n", encoding="utf-8")
    codex_dir = tmp_path / "codex"
    codex_dir.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["STATUS_FILE"] = str(statuses)
    env["QUOTE_FILE"] = str(quotes)
    env["GLYPH_FILE"] = str(glyphs)
    env["ECHO_FILE"] = str(echoes)
    env["MODE_FILE"] = str(tmp_path / "missing.txt")
    env["END_QUOTE_FILE"] = str(ends)
    env["SUBJECT_FILE"] = str(subjects)
    env["STATUS_CACHE_FILE"] = str(tmp_path / "status_cache.txt")
    env["QUOTE_CACHE_FILE"] = str(tmp_path / "quote_cache.txt")
    env["GLYPH_CACHE_FILE"] = str(tmp_path / "glyph_cache.txt")
    env["SUBJECT_CACHE_FILE"] = str(tmp_path / "subject_cache.txt")
    env["ECHO_CACHE_FILE"] = str(tmp_path / "echo_cache.txt")
    env["MODE_CACHE_FILE"] = str(tmp_path / "mode_cache.txt")
    env["END_QUOTE_CACHE_FILE"] = str(tmp_path / "end_quote_cache.txt")
    env["OUTPUT_DIR"] = str(tmp_path)
    subprocess.run([sys.executable, str(script_path)], cwd=tmp_path, check=True, env=env)
    assert not (tmp_path / "README.md").exists()
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "⚠️ mode file missing" in html


def test_rotator_handles_missing_end_quote(tmp_path):
    script_path = Path(__file__).resolve().parents[1] / "codex" / "github_status_rotator.py"
    statuses = tmp_path / "statuses.txt"
    statuses.write_text("alpha\nbeta\n", encoding="utf-8")
    quotes = tmp_path / "antenna_quotes.txt"
    quotes.write_text("echo\nnoecho\n", encoding="utf-8")
    glyphs = tmp_path / "glyphbraids.txt"
    glyphs.write_text("gamma\ndelta\n", encoding="utf-8")
    echoes = tmp_path / "echo_fragments.txt"
    echoes.write_text("sigil\nmirage\n", encoding="utf-8")
    modes = tmp_path / "modes.txt"
    modes.write_text('"a"\n"b"\n', encoding="utf-8")
    subjects = tmp_path / "subject-ids.txt"
    subjects.write_text("id1\nid2\n", encoding="utf-8")
    codex_dir = tmp_path / "codex"
    codex_dir.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["STATUS_FILE"] = str(statuses)
    env["QUOTE_FILE"] = str(quotes)
    env["GLYPH_FILE"] = str(glyphs)
    env["ECHO_FILE"] = str(echoes)
    env["MODE_FILE"] = str(modes)
    env["END_QUOTE_FILE"] = str(tmp_path / "missing.txt")
    env["SUBJECT_FILE"] = str(subjects)
    env["STATUS_CACHE_FILE"] = str(tmp_path / "status_cache.txt")
    env["QUOTE_CACHE_FILE"] = str(tmp_path / "quote_cache.txt")
    env["GLYPH_CACHE_FILE"] = str(tmp_path / "glyph_cache.txt")
    env["SUBJECT_CACHE_FILE"] = str(tmp_path / "subject_cache.txt")
    env["ECHO_CACHE_FILE"] = str(tmp_path / "echo_cache.txt")
    env["MODE_CACHE_FILE"] = str(tmp_path / "mode_cache.txt")
    env["END_QUOTE_CACHE_FILE"] = str(tmp_path / "end_quote_cache.txt")
    env["OUTPUT_DIR"] = str(tmp_path)
    subprocess.run([sys.executable, str(script_path)], cwd=tmp_path, check=True, env=env)
    assert not (tmp_path / "README.md").exists()
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "⚠️ end quote file missing" in html


def extract_quote(text: str) -> str:
    for line in text.splitlines():
        if "📡" in line:
            return line.split("“")[1].split("”")[0]
    raise AssertionError("quote not found")


def test_rotator_respects_quote_cache(tmp_path):
    random.seed(0)
    script_path = Path(__file__).resolve().parents[1] / "codex" / "github_status_rotator.py"
    statuses = tmp_path / "statuses.txt"
    statuses.write_text("alpha\n", encoding="utf-8")
    quotes = tmp_path / "antenna_quotes.txt"
    quotes.write_text("one\ntwo\n", encoding="utf-8")
    glyphs = tmp_path / "glyphbraids.txt"
    glyphs.write_text("g\nh\n", encoding="utf-8")
    echoes = tmp_path / "echo_fragments.txt"
    echoes.write_text("sig\nmir\n", encoding="utf-8")
    modes = tmp_path / "modes.txt"
    modes.write_text('"m"\n', encoding="utf-8")
    ends = tmp_path / "end-quotes.txt"
    ends.write_text("x\ny\n", encoding="utf-8")
    subjects = tmp_path / "subject-ids.txt"
    subjects.write_text("id\n", encoding="utf-8")
    codex_dir = tmp_path / "codex"
    codex_dir.mkdir(exist_ok=True)
    cache = tmp_path / "cache.txt"
    env = os.environ.copy()
    env.update({
        "STATUS_FILE": str(statuses),
        "QUOTE_FILE": str(quotes),
        "GLYPH_FILE": str(glyphs),
        "ECHO_FILE": str(echoes),
        "MODE_FILE": str(modes),
        "END_QUOTE_FILE": str(ends),
        "SUBJECT_FILE": str(subjects),
        "OUTPUT_DIR": str(tmp_path),
        "STATUS_CACHE_FILE": str(tmp_path / "status_cache.txt"),
        "QUOTE_CACHE_FILE": str(cache),
        "GLYPH_CACHE_FILE": str(tmp_path / "glyph_cache.txt"),
        "SUBJECT_CACHE_FILE": str(tmp_path / "subject_cache.txt"),
        "ECHO_CACHE_FILE": str(tmp_path / "echo_cache.txt"),
        "MODE_CACHE_FILE": str(tmp_path / "mode_cache.txt"),
        "END_QUOTE_CACHE_FILE": str(tmp_path / "end_quote_cache.txt"),
    })
    subprocess.run([sys.executable, str(script_path)], cwd=tmp_path, check=True, env=env)
    assert not (tmp_path / "README.md").exists()
    first = extract_quote((tmp_path / "index.html").read_text(encoding="utf-8"))
    subprocess.run([sys.executable, str(script_path)], cwd=tmp_path, check=True, env=env)
    second = extract_quote((tmp_path / "index.html").read_text(encoding="utf-8"))
    assert first != second


def extract_status(text: str) -> str:
    import re
    m = re.search(r"<strong>([^<]+)</strong><br>", text)
    if not m:
        raise AssertionError("status not found")
    return m.group(1)


def test_batch_cycle_no_repeats(tmp_path):
    script_path = Path(__file__).resolve().parents[1] / "codex" / "github_status_rotator.py"
    statuses = tmp_path / "statuses.txt"
    statuses.write_text("alpha\nbeta\n", encoding="utf-8")
    quotes = tmp_path / "antenna_quotes.txt"
    quotes.write_text("q1\nq2\n", encoding="utf-8")
    glyphs = tmp_path / "glyphbraids.txt"
    glyphs.write_text("g1\ng2\n", encoding="utf-8")
    echoes = tmp_path / "echo_fragments.txt"
    echoes.write_text("e1\ne2\n", encoding="utf-8")
    modes = tmp_path / "modes.txt"
    modes.write_text('"m1"\n"m2"\n', encoding="utf-8")
    ends = tmp_path / "end-quotes.txt"
    ends.write_text("x\ny\n", encoding="utf-8")
    subjects = tmp_path / "subject-ids.txt"
    subjects.write_text("s1\ns2\n", encoding="utf-8")
    env = os.environ.copy()
    env.update({
        "STATUS_FILE": str(statuses),
        "QUOTE_FILE": str(quotes),
        "GLYPH_FILE": str(glyphs),
        "ECHO_FILE": str(echoes),
        "MODE_FILE": str(modes),
        "END_QUOTE_FILE": str(ends),
        "SUBJECT_FILE": str(subjects),
        "OUTPUT_DIR": str(tmp_path),
        "STATUS_CACHE_FILE": str(tmp_path / "status_cache.txt"),
        "QUOTE_CACHE_FILE": str(tmp_path / "quote_cache.txt"),
        "GLYPH_CACHE_FILE": str(tmp_path / "glyph_cache.txt"),
        "SUBJECT_CACHE_FILE": str(tmp_path / "subject_cache.txt"),
        "ECHO_CACHE_FILE": str(tmp_path / "echo_cache.txt"),
        "MODE_CACHE_FILE": str(tmp_path / "mode_cache.txt"),
        "END_QUOTE_CACHE_FILE": str(tmp_path / "end_quote_cache.txt"),
        "STATUS_CACHE_LIMIT": "2",
        "QUOTE_CACHE_LIMIT": "2",
        "GLYPH_CACHE_LIMIT": "2",
        "SUBJECT_CACHE_LIMIT": "2",
        "ECHO_CACHE_LIMIT": "2",
        "MODE_CACHE_LIMIT": "2",
        "END_QUOTE_CACHE_LIMIT": "2",
    })
    subprocess.run([sys.executable, str(script_path)], cwd=tmp_path, check=True, env=env)
    first = extract_status((tmp_path / "index.html").read_text(encoding="utf-8"))
    subprocess.run([sys.executable, str(script_path)], cwd=tmp_path, check=True, env=env)
    second = extract_status((tmp_path / "index.html").read_text(encoding="utf-8"))
    assert first != second
