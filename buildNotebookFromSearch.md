# Build a Notebook from Article Search

Feature spec for creating a new notebook directly from article-search results,
letting the user pick which articles become sources, and reporting which
articles were ingested successfully vs. which failed.

Status: **Design / not yet implemented.**
Primary surface: the React front-end (`discoveryPortalReact`). **No backend
changes are required** — the flow is orchestrated client-side over existing
endpoints. A future optional backend batch endpoint is noted at the end.

---

## 1. User stories

### Story A — Start notebook creation from search results

```
Given  I am using article search
When   I click "Create notebook"
Then   the system notes all the articles in the search results
And    it lets me create a notebook and select which articles
       should be added as sources to the notebook.
```

### Story B — Create the notebook and ingest the selected sources

```
Given  I am creating a notebook from article-search sources
And    I have selected 1 or many articles
When   I click "Create notebook"
Then   the system:
         - creates the notebook record
         - creates a notebook source record for each selected article
And    when the process finishes, the system reports:
         - articles added with no issues
         - articles that could NOT be ingested (with the reason)
```

---

## 2. Scope & assumptions

- Each selected article becomes a **URL source** (`source_type = "url"`). The
  backend fetches and extracts the page content during import.
- The flow lives on the existing **Article Search** page
  (`src/pages/ArticleSearchPage.tsx`).
- At least **one** article must be selected to create the notebook from search.
  (Creating an empty notebook is still possible via the normal "New notebook"
  page — out of scope here.)
- Ingestion is **best-effort per article**: a single failed article must not
  abort the whole operation. The notebook and all successful sources persist.
- Indexing for Q&A (vector ingest) is **not** part of this flow. After creation
  the user can index from the notebook page as usual. (Mentioned as a follow-up
  prompt in the summary screen.)

---

## 3. Relevant existing API endpoints

| Purpose | Method & path | Request | Response |
| --- | --- | --- | --- |
| Search articles | `POST /articles/search` | `{ question, max_results }` | `{ robust_articles: [{ title, link }] }` |
| Create notebook | `POST /api/notebooks` | `{ name, description?, tags? }` | `NotebookResponse` (incl. `id`) |
| Import URL source | `POST /api/sources/url` | `{ notebook_id, url, title? }` | `SourceResponse` on 201; error envelope on failure |

Front-end wrappers already exist:
`articleApi.search`, `notebooksApi.create`, `sourcesApi.importUrl`
(in `src/api/services.ts`), plus the `useImportUrlSource` mutation hook.

> **Not used here:** `POST /api/sources/search-and-add`. That endpoint re-runs
> its own search by phrase and adds the top-N results — it does **not** accept a
> user-curated list of specific articles, which is the core of this feature.

### Failure shapes to expect from `POST /api/sources/url`

The client must translate these into a per-article "could not ingest" reason:

- `400` — validation (e.g. malformed URL).
- `409` — duplicate (same content hash already in the notebook).
- `422` / `5xx` — fetch failed, page unreachable, extraction failed, timeout.
- Network error / thrown `ApiError` — surfaced via `ApiError.message`.

---

## 4. UX flow & screen states

The Article Search page gains a small **state machine**:

```
results ──"Create notebook"──▶ select ──"Create notebook"──▶ creating ──▶ summary
   ▲                              │                                          │
   └───────────── cancel ─────────┘                  "Done" / "Open notebook"┘
```

### State: `results` (existing)
- Search returns articles (unchanged).
- **New:** when there is ≥1 result, show a **"Create notebook"** button above
  the results list.

### State: `select`
- Each article row gets a **checkbox** (all selected by default).
- A **"Select all / none"** toggle and a live count ("4 of 7 selected").
- A **notebook details** form:
  - `name` (required) — **prefilled** with the search question (trimmed,
    truncated to 255 chars), user-editable.
  - `description` (optional) — defaults to e.g. `"Created from article search:
    \"<question>\""`.
  - `tags` (optional, comma-separated).
- Primary button **"Create notebook"** — disabled unless `name` is non-empty
  **and** ≥1 article is selected.
- Secondary button **"Cancel"** — returns to `results`, selection discarded.

### State: `creating`
- All controls disabled.
- Progress indicator: **"Adding source 3 of 5…"** (and the notebook-creation
  step before it: "Creating notebook…").
- No cancel during this phase in v1 (kept simple; see Open questions).

### State: `summary`
- Headline: **"Notebook created — N of M articles added."**
- ✅ **Added with no issues** — list of `{ title, link }`.
- ⚠️ **Could not be ingested** — list of `{ title, link, reason }`.
- Actions:
  - **Open notebook** → navigate to `/notebooks/:id`.
  - **Retry failed** (optional, see §8) → re-attempt only the failed articles
    against the now-existing notebook.
  - **Done** → back to a clean search page.

---

## 5. Data flow / sequence

```
User clicks "Create notebook" (select state)
        │
        ▼
1. notebooksApi.create({ name, description, tags })
        │  success ──▶ notebook.id
        │  failure ──▶ STOP. Show error, stay in `select` state. No sources created.
        ▼
2. For each selected article (sequential, see §6):
        sourcesApi.importUrl({ notebook_id: notebook.id, url, title })
            success ──▶ push to `added`   (record source_id)
            failure ──▶ push to `failed`  (record reason from ApiError.message)
        update progress counter
        ▼
3. Build report → transition to `summary` state.
4. Invalidate React Query caches: notebooks list, this notebook, its sources.
```

Key rule: **notebook creation is the gate.** If step 1 fails, nothing else
runs. If step 1 succeeds, the notebook exists regardless of how many sources
ingest — so the summary always offers "Open notebook".

---

## 6. Concurrency

URL import does server-side fetch + content extraction, so each call can take
several seconds.

- **v1 recommendation: sequential** (one article at a time).
  - Gives an accurate "x of N" progress readout.
  - Gentle on the backend (no fan-out of slow fetches).
  - Simple, deterministic ordering of the report.
- **Optional optimization:** a bounded pool (concurrency 2–3) using
  `Promise.allSettled` over batches. Faster for large selections at the cost of
  a coarser progress indicator. Defer unless selections are routinely large.

Either way, use per-item error isolation — never `Promise.all` (which rejects
on the first failure and would mask the rest).

---

## 7. Result reporting (the report object)

```ts
interface AddedArticle {
  title: string;
  link: string;
  sourceId: string;
}

interface FailedArticle {
  title: string;
  link: string;
  reason: string; // ApiError.message, e.g. "Duplicate source", "Failed to fetch URL"
}

interface BuildResult {
  notebookId: string;
  notebookName: string;
  added: AddedArticle[];
  failed: FailedArticle[];
  totalSelected: number; // added.length + failed.length
}
```

The `summary` screen renders `added` and `failed` directly. This satisfies the
Story B reporting requirement: "articles added with no issues" and "list
articles that could not be ingested".

---

## 8. Edge cases & decisions

| Case | Behavior |
| --- | --- |
| Notebook name collides (duplicate per user) | `create` returns 409 → stay in `select`, show "A notebook with that name already exists." No sources created. |
| All selected articles fail to ingest | Notebook still created (empty). Summary shows 0 added + full failure list. Offer **Retry failed** and **Open notebook**. |
| Duplicate article (same content hash) | Counts as a `failed` item with reason "Already in notebook" (from 409). Notebook + other sources unaffected. |
| User navigates away during `creating` | In-flight + completed imports persist server-side. v1: warn via `beforeunload`/route guard is optional; simplest is to let it complete. |
| Search returns 0 results | "Create notebook" button hidden. |
| Zero selected in `select` state | "Create notebook" disabled. |
| Same article appears twice in results | De-dupe selection by `link` before importing. |
| Retry failed | Re-run §5 step 2 for `failed` items only, against the existing `notebookId`; merge into the report. |

---

## 9. Front-end implementation plan (React)

New / changed files under `discoveryPortalReact/src`:

- **`hooks/useBuildNotebookFromArticles.ts`** *(new)* — orchestrator. Exposes
  `run(params)` and reactive `{ phase, progress, result, error }`. Internally:
  `notebooksApi.create` → sequential `sourcesApi.importUrl` loop with
  `try/catch` per item building `added`/`failed` → invalidate query keys
  (`['notebooks']`, `qk.notebook(id)`, `qk.sources(id)`).
- **`pages/articleSearch/CreateNotebookFromResults.tsx`** *(new)* — the
  `select`/`creating`/`summary` panel: checkboxes, select-all, notebook detail
  form, progress, and the summary lists with reasons + "Open notebook".
- **`pages/ArticleSearchPage.tsx`** *(change)* — add the "Create notebook" CTA
  above results; mount the panel and pass the current `robust_articles` and the
  search `question` (for the prefilled name/description).

Reuses existing: `articleApi`, `notebooksApi`, `sourcesApi`, `ApiError`
(for `.message`), `ErrorMessage`, `Spinner`, query keys in `hooks/queries.ts`.

No new dependencies. No backend changes.

---

## 10. Acceptance criteria

- [ ] On the Article Search page with ≥1 result, a **"Create notebook"** action
      is visible.
- [ ] Clicking it shows all current search-result articles, each selectable,
      plus a notebook name/description/tags form (name prefilled from the query).
- [ ] "Create notebook" is disabled until a name is entered and ≥1 article is
      selected.
- [ ] On submit, exactly one notebook record is created.
- [ ] One URL source is created per **selected** article (not the unselected
      ones).
- [ ] A single article failing to ingest does not abort the others.
- [ ] When done, the user sees a report listing **added** articles and
      **failed** articles **with reasons**.
- [ ] The user can open the newly created notebook from the report.
- [ ] If notebook creation itself fails, no sources are created and the error is
      shown.

---

## 11. Future enhancements (optional, backend)

A dedicated batch endpoint would make the operation atomic-ish and faster, and
move per-article error handling server-side:

```
POST /api/notebooks/from-articles
{
  "name": "...",
  "description": "...",
  "tags": ["..."],
  "articles": [{ "title": "...", "url": "..." }]
}
→ 201 {
  "notebook": { ...NotebookResponse },
  "added":  [{ "title", "url", "source_id" }],
  "failed": [{ "title", "url", "error" }]
}
```

This mirrors the existing `AddSourcesBySearchResponse` shape (see
`search-and-add`) but takes a **curated article list** instead of re-searching.
The front-end report logic (§7) maps onto it 1:1, so adopting it later would not
change the UX. Until then, the client-side orchestration in §5 is sufficient.

---

## 12. Open questions

1. **Cancel during ingestion** — It would be cool to enable a cancel operation.
2. **Auto-index after creation** — should the summary offer a one-click "Index
   for Q&A" (vector ingest) right there, or leave it to the notebook page?
      - yes
3. **Concurrency** — ship sequential v1, or go straight to a bounded pool?
  - ship sequential

4. **Empty-notebook cleanup** — if 0 sources succeed, offer to delete the empty
   notebook, or always keep it?
    - yes
    
