# 💮 Collectivist

**AI-powered curator** for intentional collectors.<br> 
*[Work in Progress]* Exploring how to transform semantically coherent hoards into beautiful living documentation substrates with LLM-powered organization and curation.

## 🌱 Planned Features

- **Domain-specific intelligence**: Git metadata, ID3 tags, EXIF data, citations, and semantic understanding
- **LLM-powered analysis**: Bespoke categorization and rich description generation (perfect context for agents)
- **Self-healing documentation**: Collection indices that adapt to filesystem changes using semantic diffing and persisted structural memory
- **Flexible configuration**: All OpenAI compatible providers supported - local (LM Studio, Ollama), cloud (OpenRouter, Pollinations), or custom endpoints
- **Multi-format outputs**: Markdown documentation, interactive HTML index, JSON export
- **Collection types**: Repositories, Obsidian vaults, documents, media files, research papers, creative projects, datasets

## 🚧 Current Status

**Repository collections** are partially implemented with basic indexing and description generation. The broader vision of multi-format collection support, plugin architecture, and distributed coordination is in active development.

See [.kiro/specs/collectivist/](/.kiro/specs/collectivist/) for detailed requirements and design documentation.

## Installation

### 🧺 Experimental Build (Repository Collections Only)
#### Clone repo to try the current repository indexing implementation. 

*Note: Only repository collections are currently functional. Other collection types are planned.*

---

### 🎮 Full Installation (Coming Eventually)
```bash
# Planned: pip install collectivist
# collectivist init ~/my-collection --standard
```
*The complete multi-collection system with interactive UI, curation loops, and automation is in development.*
---

### 🤖 Configuration

- Current implementation works with LM Studio and other OpenAI-compatible endpoints. Configuration is evolving as the system develops.

### ⚠️ Development Warning

This is experimental software. Expect breaking changes and incomplete features as the architecture evolves.

## Collection Schema (Planned)

#### Collection Types (In Development)
- **Repositories**: Git-aware scanning, commit summaries, category taxonomy *(partially implemented)*
- **Research**: Citation extraction, topic clustering, reading status *(planned)*
- **Media**: Timeline organization, mood/genre inference, EXIF metadata *(planned)*
- **Creative**: Version tracking, asset linking, format intelligence *(planned)*
- **Datasets**: Schema inference, sample previews, data provenance *(planned)*
- **Documents**: Text extraction, metadata parsing, content analysis *(planned)*

The `collection.yaml` schema is evolving as different collection types are implemented.

**Repository Collection Example:**
```yaml
collection_type: repositories
status: "✓"                    # Status glyph for up-to-date repos
name: my-repos
path: /path/to/repos
categories:
  - phext_hyperdimensional     # Multi-dimensional text systems
  - ai_llm_agents             # AI agents and LLM infrastructure
  - terminal_ui               # Terminal UI frameworks and components
  - creative_aesthetic        # Art, music, visualization tools
  - dev_tools                 # Development utilities and build tools
  - esoteric_experimental     # Experimental and occult systems
  - system_infrastructure     # System-level networking tools
  - utilities_misc            # General utilities and miscellaneous
exclude_hidden: true
scanner_config:
  always_pull: {}             # Repos to auto-pull: {repo_name: true}
  fetch_timeout: 30           # Git fetch timeout in seconds
```

**Media Collection Example:**
```yaml
collection_type: media
status: "🎵"                   # Status glyph for media collections
name: my-media
path: /path/to/media
categories:
  - music_albums              # Full album collections
  - music_singles             # Individual tracks
  - video_movies              # Movie files
  - video_series              # TV series and episodes
  - images_photos             # Photography collections
  - images_artwork            # Digital art and graphics
exclude_hidden: true
scanner_config:
  extract_metadata: true      # Extract ID3, EXIF, etc.
  supported_formats:          # File extensions to scan
    audio: [".mp3", ".flac", ".wav", ".m4a"]
    video: [".mp4", ".mkv", ".avi", ".mov"]
    image: [".jpg", ".png", ".gif", ".webp"]
```

## 🔌 Plugin Architecture (In Development)

**Planned Plugin System:** Collectivist will include domain-specific plugins for different collection types. The plugin architecture is being designed to automatically select appropriate plugins based on collection type detection.

**Development Status:**
- **repositories** - Basic implementation exists *(functional but evolving)*
- **obsidian vaults** - Planned
- **media libraries** - Planned  
- **document libraries** - Planned

**Plugin Discovery:** The automatic collection type detection and plugin routing system is in development.

**Custom Plugins:** Plugin interface is being designed - see specs for current architecture plans.

## 🔗 Workflow Stages

### Stage 1: Indexer (deterministic)

Initialize for a specific type of library or get a custom schema. 

Discovers items and note metadata using domain-specific plugins.

### Stage 2: Describer (LLM)

Generates LLM descriptions and collection overview with concurrent workers.

## Contributing

Issues and PRs welcome! This is an exploration of collection-first AI curation.

## License

Private research tool - not for distribution.

---

*Infrastructure as palimpsest, data as compiled breath 🜍*
