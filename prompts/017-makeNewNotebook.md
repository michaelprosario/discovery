- Amend /workspaces/discovery/scripts/ingest_wikipedia_notebook.py
- Change program so we create a new notebook on each run.
- Address this error:

@michaelprosario ➜ /workspaces/discovery (feat/vector_db) $ python src/apps/ingest_notebook_into_vectordb.py 
[*] Starting ingestion for notebook: e1b92408-5295-433f-9b8a-6f9fe6a68f1f
    Collection: ben_franklin
    Chunk size: 1000, Overlap: 200
    Force reingest: False

[ERROR] Ingestion failed: Notebook with ID e1b92408-5295-433f-9b8a-6f9fe6a68f1f not found
