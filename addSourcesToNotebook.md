# Add Sources to an Existing Notebook from Article Search

Feature spec for adding sources to a notebook the user is **already
reviewing**, by searching for articles, selecting one or many results, and
clicking **"Add sources to notebook"** — then reporting which articles were
ingested successfully vs. which could not be.

Status: **Design / not yet implemented.**
Primary surface: the React front-end (`discoveryPortalReact`), on the notebook
detail page (`src/pages/NotebookDetailPage.tsx`). **No backend changes are
required** — the flow is orchestrated client-side over existing endpoints.

> Sibling feature: [`buildNotebookFromSearch.md`](./buildNotebookFromSearch.md)
> covers the *create-a-new-notebook-from-search* flow (already implemented as
> `hooks/useBuildNotebookFromArticles.ts` + `pages/articleSearch/CreateNotebookFromResults.tsx`).
> This feature is the same per-article ingest + report pattern, **minus the
> notebook-creation gate** — the notebook already exists. The two should share
> the ingest core (see §9).

---

## 1. User story

```
Given  I am reviewing an existing notebook
And    I have populated a search term in the search field
And    I have clicked "Search"
And    the system has rendered a list of articles
And    I have selected 1 or many sources for notebook creation
When   I click "Add sources to notebook"
Then   the system:
         - creates a notebook source record for each selected article
And    when the process finishes, the system reports:
         - articles added with no issues
         - articles that could NOT be ingested (with the reason)
```

---

## 2. Scope & assumptions

- The notebook **already exists**. There is no create/notebook-details form and
  no "notebook creation is the gate" step — the gate from the sibling feature
  is removed.
- Each selected article becomes a **URL source** (`source_type = "url"`). The
  backend fetches and extracts the page content during import
  (`POST /api/sources/url`).
- The search and selection UI lives **inside the notebook detail page's
  "Sources" tab**, alongside the existing `AddSourcePanel` (single-source add).
  It is a new, complementary way to add many sources at once.
- The article search is **not** notebook-aware on the backend — it is the same
  `POST /articles/search`. The only notebook-specific input is the
  `notebook_id` we pass to each `POST /api/sources/url` call.
- At least **one** article must be selected before "Add sources to notebook" is
  enabled.
- Ingestion is **best-effort per article**: a single failed article must not
  abort the whole operation. Every successful source persists.
- Indexing for Q&A (vector ingest) is **not** part of this flow, but the summary
  may offer a one-click "Index for Q&A" (the notebook page already exposes
  `useIngestNotebook` via `IndexPanel`).

---

## 3. Relevant existing API endpoints

| Purpose | Method & path | Request | Response |
| --- | --- | --- | --- |
| Search articles | `POST /articles/search` | `{ question, max_results }` | `{ robust_articles: [{ title, link }] }` |
| Import URL source | `POST /api/sources/url` | `{ notebook_id, url, title? }` | `Source` on 201; error envelope on failure |

Front-end wrappers already exist (`src/api/services.ts`):

- `articleApi.search(body: ArticleSearchRequest): Promise<ArticleSearchResponse>`
- `sourcesApi.importUrl(body: ImportUrlSourceRequest): Promise<Source>`

Relevant types (`src/api/types.ts`):

```ts
interface ArticleResult { title: string; link: string; }
interface ArticleSearchResponse { robust_articles: ArticleResult[]; }
interface ImportUrlSourceRequest { notebook_id: string; url: string; title?: string; }
```

### Failure shapes to expect from `POST /api/sources/url`

The client must translate these into a per-article "could not ingest" reason
(via `ApiError.message`):

- `400` — validation (e.g. malformed URL).
- `409` — duplicate (same content hash already in the notebook → "Already in
  notebook").
- `422` / `5xx` — fetch failed, page unreachable, extraction failed, timeout.
- Network error / thrown `ApiError` — surfaced via `ApiError.message`.

---

## 4. UX flow & screen states

A new panel on the **Sources** tab of `NotebookDetailPage`. It has its own
small state machine — note there is **no `creating-notebook` phase**:

```
search ──"Search"──▶ results ──select──▶ "Add sources" ──▶ adding ──▶ summary
   ▲                                                                     │
   └───────────────────────── Done / close ─────────────────────────────┘
```

### State: `search` (entry)
- A search field (question/topic) + "Max results" + a **"Search"** button.
- Mirrors `ArticleSearchPage`'s form (reuse the same inputs/labels).

### State: `results`
- Search returns articles. Each article row gets a **checkbox**.
- Default selection: **all results selected** (matches the sibling feature).
- A **"Select all / none"** toggle and a live count ("4 of 7 selected").
- Primary button **"Add sources to notebook"** — disabled unless ≥1 article is
  selected.
- "Search again" lets the user run a new query (clears results + selection).
- 0 results → show "No articles found." and hide the add button.

### State: `adding`
- All controls disabled.
- Progress indicator: **"Adding source 3 of 5…"**.
- A **Cancel** button (stops before the next article; an in-flight import is
  allowed to finish server-side — same semantics as the sibling hook).

### State: `summary`
- Headline: **"N of M article(s) added."** (`+ " (cancelled)"` if cancelled).
- ✅ **Added with no issues** — list of `{ title, link }`.
- ⚠️ **Could not be ingested** — list of `{ title, link, reason }`.
- Actions:
  - **Add more sources** → back to `search` (clean), notebook unchanged.
  - **Retry failed** (if any) → re-attempt only the failed articles against the
    same notebook; merge into the report.
  - **Index for Q&A** (optional, if ≥1 added) → `useIngestNotebook(notebookId)`.
  - **Done / Close** → collapse the panel; the `SourceList` below now reflects
    the new sources (caches invalidated, see §5).

---

## 5. Data flow / sequence

```
User clicks "Search" (search state)
        │ articleApi.search({ question, max_results }) ──▶ robust_articles
        ▼
results state: user selects articles, clicks "Add sources to notebook"
        ▼
For each selected article (sequential, see §6):
        sourcesApi.importUrl({ notebook_id, url: article.link, title: article.title })
            success ──▶ push to `added`  (record source.id)
            failure ──▶ push to `failed` (record reason from ApiError.message)
        update progress counter
        ▼
Build report → transition to `summary` state.
Invalidate React Query caches:
        qk.sources(notebookId), qk.notebook(notebookId), qk.vectorCount(notebookId)
```

Unlike the create flow, there is **no preliminary gate** — the notebook already
exists, so import begins immediately on "Add sources to notebook".

---

## 6. Concurrency

URL import does server-side fetch + content extraction, so each call can take
several seconds.

- **v1: sequential** (one article at a time) — accurate "x of N" progress,
  gentle on the backend, deterministic report ordering. (Matches the sibling
  hook's `importArticles` loop exactly.)
- **Optional later:** a bounded pool (concurrency 2–3) over batches with
  per-item error isolation. Defer.

Always use per-item `try/catch` (the sibling hook's pattern) — never
`Promise.all` (which rejects on the first failure and masks the rest).

---

## 7. Result reporting (the report object)

Reuse the sibling hook's shapes verbatim, dropping notebook-name fields the
caller already knows:

```ts
interface AddedArticle  { title: string; link: string; sourceId: string; }
interface FailedArticle { title: string; link: string; reason: string; }

interface AddSourcesResult {
  notebookId: string;
  added: AddedArticle[];
  failed: FailedArticle[];
  /** True when the user cancelled before every selected article was processed. */
  cancelled: boolean;
}
```

The `summary` screen renders `added` and `failed` directly — satisfying the
requirement: "articles added with no issues" and "list articles that could not
be ingested."

---

## 8. Edge cases & decisions

| Case | Behavior |
| --- | --- |
| Search returns 0 results | "Add sources to notebook" hidden; show "No articles found." |
| Zero selected | "Add sources to notebook" disabled. |
| Same article appears twice in results | De-dupe selection by `link` before importing (`dedupeByLink`). |
| Article already a source in this notebook | `409` → a `failed` item with reason "Already in notebook". Other sources unaffected. |
| One article fails to ingest | Per-item isolation; the rest continue. |
| User cancels mid-run | Stop before the next article; in-flight import finishes server-side. Unprocessed remainder reported as failed with reason "Cancelled". |
| User navigates away during `adding` | In-flight + completed imports persist server-side. v1: let it complete; no route guard required. |
| All selected articles fail | Summary shows 0 added + full failure list. Offer **Retry failed**. (No "delete empty notebook" — the notebook pre-existed and is not ours to delete.) |
| Search errors | Show `ErrorMessage`; stay in `search` state. |

---

## 9. Front-end implementation plan (React)

The cleanest path **refactors the shared ingest core out of
`useBuildNotebookFromArticles.ts`** so both features use one implementation.

### Option A (recommended) — extract a shared hook

`useBuildNotebookFromArticles` already contains an `importArticles(notebookId,
articles)` helper that does exactly step 2 of this feature (sequential
per-article `sourcesApi.importUrl` with `added`/`failed` isolation, progress,
cancel, and `retryFailed`). Extract it:

- **`hooks/useAddSourcesToNotebook.ts`** *(new)* — owns `importArticles`, the
  `phase` (`'idle' | 'adding-sources' | 'done'`), `progress`, `result`,
  `cancel`, `reset`, `retryFailed`, and cache invalidation. Exposes
  `run({ notebookId, articles })`.
- **`hooks/useBuildNotebookFromArticles.ts`** *(change)* — keep the
  notebook-creation gate, then **delegate** the import to the shared core (or
  internally call `useAddSourcesToNotebook`'s logic). No behavior change to the
  create flow.

### Option B (lower-risk, mild duplication)

Leave `useBuildNotebookFromArticles` untouched; create
`hooks/useAddSourcesToNotebook.ts` as a trimmed copy (no `creating-notebook`
phase, no `notebooksApi.create`, no `delete empty notebook`). Faster to ship;
costs a second copy of the ~40-line import loop.

### UI components

- **`pages/notebook/AddSourcesFromSearch.tsx`** *(new)* — the panel with the
  `search` / `results` / `adding` / `summary` states: search form, result
  checkboxes, select-all, progress, and the summary lists with reasons. Takes
  `{ notebookId }`. Reuses `CreateNotebookFromResults`'s summary markup and
  `CreateNotebookFromResults.module.css` (or a shared `ReportList` component —
  see below).
- **`pages/NotebookDetailPage.tsx`** *(change)* — in the `sources` tab, mount
  the new panel next to `AddSourcePanel`, e.g. a collapsible
  **"Find sources on the web"** section above/below `+ Add source`.

### Optional shared presentational component

The added/failed summary lists are identical between this feature and
`CreateNotebookFromResults`. Consider extracting
**`components/IngestReport.tsx`** (`{ added, failed }`) and reusing it in both
to avoid drift.

Reuses existing: `articleApi`, `sourcesApi`, `ApiError` (for `.message`),
`ErrorMessage`, `Spinner`, `useIngestNotebook`, query keys in
`hooks/queries.ts`.

No new dependencies. No backend changes.

---

## 10. Acceptance criteria

- [ ] On a notebook's **Sources** tab, the user can enter a search term and
      click **"Search"**, and the system renders a list of articles.
- [ ] Each article is selectable (checkbox); the user can select 1 or many.
- [ ] **"Add sources to notebook"** is disabled until ≥1 article is selected.
- [ ] On click, one URL source is created per **selected** article (not the
      unselected ones), against the **existing** notebook — no new notebook is
      created.
- [ ] A single article failing to ingest does not abort the others.
- [ ] When done, the user sees a report listing **added** articles and
      **failed** articles **with reasons**.
- [ ] The new sources appear in the notebook's `SourceList` (caches
      invalidated).
- [ ] The user can retry failed articles and (optionally) index for Q&A from the
      summary.

---

## 11. Future enhancements (optional, backend)

A dedicated batch endpoint would make the operation faster and move per-article
error handling server-side. It would mirror the create-flow proposal in
`buildNotebookFromSearch.md` §11, but target an **existing** notebook:

```
POST /api/notebooks/{notebook_id}/sources/from-articles
{ "articles": [{ "title": "...", "url": "..." }] }
→ 200 {
  "added":  [{ "title", "url", "source_id" }],
  "failed": [{ "title", "url", "error" }]
}
```

The front-end report logic (§7) maps onto it 1:1, so adopting it later would not
change the UX. Until then, the client-side orchestration in §5 is sufficient.

---

## 12. Open questions

1. **Placement** — should the search-and-add panel be its own tab, a section
   within the Sources tab, or folded into `AddSourcePanel` as a 4th "Web search"
   tab?
    it should be it's own tab



2. **Auto-index after adding** — offer one-click "Index for Q&A" on the summary,
   or leave it to `IndexPanel`?
    offer one-click "Index for Q&A" on the summary

3. **Shared core** — Option A (extract shared hook) vs Option B (copy)? Option A
   is recommended to prevent the two ingest loops from drifting.
      Option A
      
