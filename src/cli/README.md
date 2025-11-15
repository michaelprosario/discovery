# Discovery CLI

A Typer-powered command line interface for orchestrating the Discovery research system over its FastAPI backend. The CLI enables you to configure API profiles, manage notebooks and sources, trigger vector ingestion, generate outputs, and run question answering – all from a terminal session or within shell scripts.

## Installation

```bash
# from the repository root
python -m pip install -e .

# or install into an isolated environment via pipx
pipx install path/to/discovery
```

The project publishes the console script `discovery` via the entry point declared in `pyproject.toml`.

## First Run

1. Boot the Discovery FastAPI service (e.g., `scripts/dev.sh` or Docker).
2. Point the CLI at the API by creating a profile:
   ```bash
discovery config init --url http://localhost:8000 --api-key test
   ```
3. Verify connectivity:
   ```bash
   discovery config test
   ```
4. List notebooks to confirm everything is wired up:
   ```bash
   discovery notebooks list
   ```

Configuration is stored in `~/.discovery/config.toml` (override with `DISCOVERY_CONFIG_HOME`). Runtime state such as the most recently used notebook GUID lives in `state.json` in the same directory.

## Output Formats

Every resource listing command accepts `--format/--format json|yaml|text|table`. Table output (default) uses `rich`; JSON/YAML are convenient for scripting pipelines.

## Command Groups

| Command | Alias | Highlights |
| --- | --- | --- |
| `discovery config` | — | Initialise profiles, switch `--profile`, emit `.env` snippets, run health checks. |
| `discovery notebooks` | `discovery nb` | CRUD operations, tag management, recent notebook tracking, blog post generation. |
| `discovery sources` | `discovery src` | Add URL/file/text sources, list or inspect sources, delete entries. |
| `discovery vectors` | `discovery vec` | Ingest notebooks, run semantic similarity queries, count/purge vectors, create collections. |
| `discovery outputs` | `discovery out` | List/create/search outputs, preview content, delete artefacts. |
| `discovery articles` | — | Fetch candidate articles for a research question. |
| `discovery qa` | — | Ask a notebook question with RAG and view service health. |

All commands respect `--profile` to target a specific configuration profile. When a notebook GUID is not supplied the CLI falls back to the last notebook you touched (`discovery notebooks recent --set <id>` to override).

## Scripting Tips

- Use `--format json` or `--format yaml` for machine-readable responses.
- Pipe results through `jq`, e.g., `discovery notebooks list --format json | jq '.notebooks[0].id'`.
- Combine with `xargs` to batch operations: `discovery sources list -n <id> --format json | jq -r '.[] | .id' | xargs -I{} discovery sources remove {}`.

## Environment Variables

- `DISCOVERY_CONFIG_HOME`: override the configuration directory (default `~/.discovery`).
- `DISCOVERY_API_URL`, `DISCOVERY_API_KEY`, `DISCOVERY_NOTEBOOK_GUID`: produced by `discovery config env` for shell integration.

## Development Notes

- Commands live under `src/cli/commands/` and share helpers (`config_store.py`, `runtime.py`, `output.py`, `utils.py`).
- Add new command groups by creating a Typer app and registering it in `src/cli/__main__.py`.
- Integration tests can mock the API using `httpx.MockTransport` or `respx`; see `tests/cli/` (create as needed).




## discovery cli examples
  
discovery --help
discovery notebooks --help
discovery config init --url http://localhost:8000
discovery notebooks list--format json
discovery src add url --notebook 380fe8dc-73ff-4b7b-a2a2-0025905a12da --format json --url https://en.wikipedia.org/wiki/Bill_Gates
discovery vectors ingest --notebook 380fe8dc-73ff-4b7b-a2a2-0025905a12da
discovery qa ask --notebook 380fe8dc-73ff-4b7b-a2a2-0025905a12da --format json --question "When was bill gates born?"
  