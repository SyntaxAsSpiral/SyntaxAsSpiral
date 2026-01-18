# 📔 Autopoesis

**Recursive autojournaling system** for self-creation through activity tracking and LLM-powered generation.<br>
*[Work in Progress]* The framework is currently in specification phase. The reference implementation is my personal site/repo at [github.com/SyntaxAsSpiral/SyntaxAsSpiral](https://github.com/SyntaxAsSpiral/SyntaxAsSpiral).

## Concept

Autopoesis abstracts the patterns from pulse-log into a reusable framework where you can define:
- **Activity sources**: Git commits, shell history, chat logs, or custom sources
- **Field schemas**: What content to generate (status, narrative, glyphs, etc.)
- **Output targets**: Static HTML, markdown, social media, or custom destinations

The system creates a recursive feedback loop where generated content feeds back as examples, developing a consistent voice over time.

## 🚧 Current Status

**Specification phase.** Requirements and design documents are being developed. The working implementation exists in my personal site repo as a concrete instance.

See [.kiro/specs/autopoesis/](/.kiro/specs/autopoesis/) for detailed requirements and design documentation.

## 🎯 Planned Architecture

### Core Components

- **Activity Sources**: Pluggable adapters for different input streams
- **Context Aggregation**: Session grouping and LLM-ready formatting
- **Field Generation**: Batch LLM calls with recursive cache feedback
- **Output Targets**: Pluggable adapters for different destinations

### Example Instance: pulse-log

My personal implementation generates:
- **status**: Brief update on current work
- **subject**: Main focus area
- **mode**: Work mode (building, exploring, refining, integrating)
- **glyph**: Emoji representing the session essence
- **narrative**: Poetic description of the work

Output: Static HTML homepage updated with each journal entry.

## 🔗 Related Projects

- **pulse-log**: First concrete instance (dev journaling → HTML homepage)
- **collectivist**: Complementary input side (curates static collections → living indices)
- **amexsomnemon**: Memory substrate layer (the living archive)

The trinity:
- collectivist: Past (what you've collected)
- autopoesis: Present (what you're creating now)
- amexsomnemon: Memory substrate (the living archive)

## 🎮 Future Installation

```bash
# Planned: pip install autopoesis
# autopoesis init my-journal --config journal.yaml
# autopoesis run
```

*The generic framework is in development. For now, see the reference implementation.*

## Configuration Model (Planned)

Each autopoesis instance will have:
- **Source config**: Which activity sources, time windows, filters
- **Field schema**: What fields to generate, formats, constraints
- **Generation config**: Models, temperatures, batch groups, prompt templates
- **Output config**: Where to send content, formatting rules
- **Cache config**: Recursive feedback settings, sampling strategies

## Example Instances (Planned)

### pulse-log (dev journaling)
- Sources: git, shell history
- Fields: status, subject, mode, glyph, narrative
- Output: HTML homepage
- Aesthetic: pneumastructural/operator vocabulary

### social-pulse (social media presence)
- Sources: git, collectivist indices
- Fields: status, insight, link
- Output: X/Twitter, Discord
- Aesthetic: terse, hyperstitional

### project-dashboard (project status)
- Sources: git, issue trackers, CI/CD
- Fields: status, blockers, progress, next_steps
- Output: Markdown, HTML dashboard
- Aesthetic: technical, clear

## ⚠️ Development Warning

This is experimental software in early specification phase. The architecture is being designed for bespoke personal systems, not enterprise scale.

## Contributing

Issues and PRs welcome once the framework is implemented! For now, this is design exploration.

## License

Private research tool - not for distribution.

---

*Self-making through recursive poetic generation 🜍*
