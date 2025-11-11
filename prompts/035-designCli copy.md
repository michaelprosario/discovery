
- plan a cli interface for discovery notebook system
- cli should enable user  to connect to  discovery  fast api instance via configuration
- design cli patterns for notebook creation,  adding sources of different types
- cli should enable me to ask questions of notebook given the notebook guid and a prompt

---

### CLI high-level structure

```
discovery
  ├── config        # configure API endpoint and auth
  ├── notebooks     # CRUD + metadata operations
  ├── sources       # import and manage notebook sources
  ├── vectors       # ingestion + semantic search controls
  ├── outputs       # generated artifacts (blog posts, drafts)
  ├── articles      # external article discovery
  └── qa            # RAG question answering + health
```

Each command group should expose short aliases (`discovery nb`, `discovery src`) and support JSON/YAML output for scripting via `--format`.

---

### Configuration workflow (`discovery config`)

- **init**: guides the user through creating `~/.discovery/config.toml` with API URL, default notebook.
  - Flags: `--url`, `--api-key`, `--overwrite` for noninteractive runs.
  - Validates connectivity by making a lightweight `GET /health` call.
- **show**: prints the active configuration; `--raw` emits machine-readable JSON.
- **use**: switches between named profiles (e.g., `discovery config use staging`).
- **test**: pings the configured API and reports latency + auth status.
- **env**: outputs an `.env` snippet for shell integration.

---

### Notebook operations (`discovery notebooks`)

- **list** → `GET /api/notebooks`: render GUID, name, tags, source counts with `--limit`, `--offset`, `--tags`, `--sort-by` mapped to query params.
- **create** → `POST /api/notebooks`: supply `--name`, `--description`, `--tags` (comma separated) to build the `CreateNotebookRequest`; print returned notebook payload.
- **show** → `GET /api/notebooks/{id}`: optionally append `--include-sources` to chain a `GET /api/sources/notebook/{id}` call.
- **update** → `PUT /api/notebooks/{id}`: accept JSON patch file or CLI flags to populate `UpdateNotebookRequest` (description, tags, default model).
- **rename** → `PATCH /api/notebooks/{id}/rename`: shortcut for quick name change.
- **tags add/remove** → `POST|DELETE /api/notebooks/{id}/tags`: flags `--add-tag`, `--remove-tag` transform into the respective payloads.
- **delete** → `DELETE /api/notebooks/{id}`: `--cascade` toggles the `cascade` query parameter.
- **generate-blog-post** → `POST /api/notebooks/{id}/generate-blog-post`: wrap parameters such as `--tone`, `--include-links` into `GenerateBlogPostRequest` and surface the created `OutputResponse`.
- **recent**: maintain a local pointer (`~/.discovery/state.json`) to the last notebook id for command defaults.

---

### Source management (`discovery sources`)

Source subcommands share a consistent signature: `discovery sources add <type> --notebook <guid> [flags]`.

- Supported types per API: `url`, `file`, `text`.
- **add url** → `POST /api/sources/url`: `--url`, optional `--title`; CLI fetches notebook id from flag or context and posts `ImportUrlSourceRequest`.
- **add file** → `POST /api/sources/file`: read file bytes, base64 encode to satisfy `ImportFileSourceRequest.file_content`; detect mime to populate `file_type`.
- **add text** → `POST /api/sources/text`: open `$EDITOR` when content omitted; submit `ImportTextSourceRequest`.
- **list** → `GET /api/sources/notebook/{id}`: expose filters `--type`, `--file-type`, `--include-deleted`, `--limit`, `--offset`.
- **show** → `GET /api/sources/{id}`: include `--include-deleted` flag.
- **remove** → `DELETE /api/sources/{id}`: require `--notebook` to populate query; prompt before destructive action.

---

### Vector operations (`discovery vectors`)

- **ingest** → `POST /api/notebooks/{id}/ingest`: flags `--chunk-size`, `--overlap`, `--force` map to `IngestNotebookRequest`.
- **similar** → `GET /api/notebooks/{id}/similar`: expose `--query` and `--limit` to surface semantic matches (wrap in table output with similarity score).
- **count** → `GET /api/notebooks/{id}/vectors/count`: quick status call for ingestion completeness.
- **purge** → `DELETE /api/notebooks/{id}/vectors`: confirm before deleting vector embeddings.
- **collection create** → `POST /api/notebooks/{id}/collection`: useful for first-time setup; print created collection name.

---

### Output operations (`discovery outputs`)

- **list** → `GET /api/outputs`: filters `--notebook`, `--type`, `--status`, and pagination.
- **create** → `POST /api/outputs?notebook_id=...`: allow passing a JSON template or inline `--prompt`, `--type` to build `CreateOutputRequest`.
- **show** → `GET /api/outputs/{id}` (from spec section not shown above but available) to inspect metadata.
- **delete** → `DELETE /api/outputs/{id}`: enforce confirmation unless `--force` supplied.
- **preview** → `GET /api/outputs/{id}/preview`: render to stdout or write to file with `--out`.
- **search** → `GET /api/outputs/search`: expose `--query`, `--notebook`, `--type`, `--status`, plus pagination to mirror available query params.

---

### Article discovery (`discovery articles`)

- **search** → `POST /articles/search`: accept `--question` and optional `--limit`, map to `ArticleSearchRequest`, and present returned article list with titles + URLs.
- Cache recent results locally so they can be re-used when adding sources (e.g., pipe into `discovery sources add url`).

---

### Question answering (`discovery qa`)

- **ask**: `discovery qa ask --notebook <guid> --question "..."`.
  - Maps to `POST /api/notebooks/{id}/qa`; support fields from `AskQuestionRequest` such as `retrieval_limit`, `response_style` if present.
  - Output modes: `--format text|json`; JSON includes cited source IDs for downstream tooling.
- **health** → `GET /api/notebooks/qa/health`: quick diagnostic to surface model name, vector DB connectivity.

---

### Cross-cutting concerns

- **Authentication**: support API key headers now; leave OAuth as future work but keep config schema extensible.
- **Logging**: `--verbose` surfaces HTTP request traces; `--quiet` hides progress bars.
- **Context awareness**: allow commands to infer notebook GUID from recent context (`discovery notebooks create` -> set `$DISCOVERY_NOTEBOOK_GUID`).

---

### Implementation notes

- Recommended toolkit: `Typer` (Click 8+) for declarative command definitions, `rich` for formatted output, `pydantic` for config schemas.
- Structure project with an entry point (`__main__.py`) delegating to modules per command group.
- Provide integration tests that mock the FastAPI backend; use `pytest` with `respx` or `httpx.MockTransport`.
- Package for distribution via `pipx` and include autocomplete scripts (`typer` can generate `bash`, `zsh`, `fish` completions).
- CI task to run `discovery --help` and subcommand help to ensure docs stay in sync.



**Good CLI design emphasizes clarity, consistency, and user empowerment. A well-designed CLI should feel intuitive, predictable, and efficient for both beginners and power users.**

---

### 🌟 Core Principles of CLI Design

- **Consistency in Commands and Options**
  - Use predictable patterns across commands.
  - Stick to established conventions (e.g., `--help`, `--version`).
  - Avoid surprising users with irregular syntax.

- **Clear and Helpful Documentation**
  - Provide accessible help (`command --help`) with examples.
  - Include concise descriptions of commands and flags.
  - Offer error messages that explain *what went wrong* and *how to fix it*.

- **Discoverability and Learnability**
  - Support intuitive defaults so users can get started quickly.
  - Offer interactive prompts or suggestions when appropriate.
  - Make commands self-explanatory with meaningful names.

- **Sensible Defaults with Flexibility**
  - Default behavior should handle common use cases.
  - Allow customization for advanced users without overwhelming beginners.
  - Example: `git commit` defaults to opening an editor, but flags allow inline messages.

- **Human-Centered Output**
  - Output should be readable, structured, and parsable.
  - Use clear formatting (tables, indentation, color when possible).
  - Avoid cryptic or verbose responses.

- **Error Handling and Feedback**
  - Fail gracefully with actionable error messages.
  - Provide exit codes that integrate well with scripts.
  - Avoid silent failures—users should know what happened.

- **Performance and Efficiency**
  - Commands should execute quickly and avoid unnecessary overhead.
  - Support piping and scripting for automation.
  - Keep startup times minimal.

- **Accessibility and Inclusivity**
  - Ensure output works with screen readers.
  - Avoid relying solely on color for meaning.
  - Provide verbose modes for clarity.

