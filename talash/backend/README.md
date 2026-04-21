# Talash Backend Documentation

## Developer Quickstart

Run these commands from project root (`C:\Projects\Talash`), then start the backend from `talash/backend`.

1. Create and activate virtual environment (PowerShell):

```powershell
python -m venv myvenv
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned)
(& .\myvenv\Scripts\Activate.ps1)
```

2. Install backend dependencies:

```powershell
pip install -r .\talash\backend\requirements.txt
```

3. Set required environment variables in `.env` at project root:

```
OPENROUTER_API_KEY=your_openrouter_api_key
# Optional but recommended for CrossRef user-agent contact
CROSSREF_CONTACT_EMAIL=you@example.com
```

4. Start API server:

```powershell
cd .\talash\backend
uvicorn main:app --reload
```

5. Run tests:

```powershell
cd .\talash\backend
pytest -q
```

6. Open API docs after server starts:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## What This Backend Does

The backend is a FastAPI service for CV ingestion, extraction, enrichment, and retrieval.

High-level responsibilities:
- Accept PDF uploads.
- Split and parse PDF content into one or more CV text blocks.
- Extract structured candidate data with an LLM and validation schema.
- Enrich publication metadata from CrossRef.
- Store normalized candidate records in PostgreSQL.
- Expose API endpoints to list candidates, view full candidate profiles, and enrich publications on demand.


## End-to-End Data Flow

1. Client uploads a PDF to `POST /api/cv/upload`.
2. Route writes the upload to a temporary file and invokes the LangGraph pipeline.
3. Graph runs three nodes in sequence:
   - `parser` reads PDF pages and splits CV boundaries.
   - `llm_extractor` converts text into structured JSON and runs post-processing.
   - `database_storage` writes structured data to relational tables.
4. API responds with upload summary:
   - how many candidates were extracted,
   - how many were newly stored,
   - per-candidate extraction errors (if any).
5. Clients can later query:
   - `GET /api/cv/candidates` for summarized candidate records,
   - `GET /api/cv/candidates/{candidate_id}` for full profile details.
6. `POST /api/publications/enrich/{candidate_id}` can re-run publication enrichment and authorship inference for a candidate.


## Backend Folder Structure

```
backend/
  main.py
  graph.py
  schemas.py
  requirements.txt
  routers/
    __init__.py
    cv.py
    publications.py
  nodes/
    __init__.py
    parser.py
    llm_extractor.py
    database_storage.py
  services/
    __init__.py
    publication_enricher.py
  migrations/
    versions/
      add_publication_crossref_fields.py
  tests/
    __init__.py
    test_llm_extractor_helpers.py
    test_publication_enricher.py
  __pycache__/
```


## File-by-File Explanation

### `main.py`
Application bootstrap for FastAPI.

What it does:
- Creates the FastAPI app instance (`TALASH API`).
- Adds permissive CORS middleware.
- Ensures the parent package path is importable when running from inside `backend/`.
- Calls `init_db()` at startup so DB tables are initialized.
- Registers route modules:
  - CV routes at `/api/cv`
  - Publication routes at `/api/publications`

Why it matters:
- This is the runtime entrypoint used by Uvicorn.


### `graph.py`
Defines the extraction workflow graph using LangGraph.

What it does:
- Declares graph state (`CVState`) with keys:
  - `pdf_path`
  - `raw_texts`
  - `all_results`
  - `error`
- Adds and wires three nodes in strict order:
  1. `parser`
  2. `llm_extractor`
  3. `database_storage`
- Compiles the graph (`app = g.compile()`).

Why it matters:
- Central orchestration logic for the backend extraction pipeline.


### `schemas.py`
Pydantic response models for API output contracts.

What it contains:
- Upload summary model (`UploadSummaryResponse`).
- Candidate summary and list item models.
- Full candidate profile models with nested education, experience, publications, skills, books, patents, supervised students.

Why it matters:
- Keeps API responses validated, explicit, and stable for frontend clients.


### `requirements.txt`
Python dependencies required specifically by the backend.

Important packages:
- API layer: `fastapi`, `uvicorn`, `python-multipart`
- ORM/DB: `sqlalchemy`, `psycopg2-binary`
- LLM flow: `langgraph`, `langchain-openai`, `langchain-anthropic`
- PDF parsing: `pymupdf`
- Validation/config: `pydantic`, `python-dotenv`
- Utility/data/testing: `pandas`, `openpyxl`, `requests`, `pytest`


## Routers

### `routers/__init__.py`
Empty package marker.

Why it exists:
- Makes `routers` importable as a Python package.


### `routers/cv.py`
Core CV API endpoints.

Endpoints:

1. `POST /upload`
- Validates file extension is PDF.
- Stores upload in a temporary file.
- Invokes the graph pipeline.
- Computes before/after candidate counts.
- Returns extraction/stored summary and extraction errors.
- Cleans up temp file and uploaded stream in `finally`.

2. `GET /candidates`
- Returns list of candidates with summary counts and nested details.
- Uses `selectinload` to reduce N+1 ORM query behavior.

3. `GET /candidates/{candidate_id}`
- Returns full profile for one candidate.
- Includes all major relations.
- Normalizes experience dates to `YYYY-MM` using `_to_yyyy_mm` helper.

Why it matters:
- Main interface for upload and candidate retrieval used by frontend or API clients.


### `routers/publications.py`
Publication enrichment endpoint.

Endpoint:
- `POST /enrich/{candidate_id}`

What it does:
- Loads candidate by external candidate id.
- Fetches all publications for candidate.
- Builds enrichment payload.
- Calls:
  - `enrich_publications(...)` for CrossRef-based metadata fill.
  - `infer_authorship_roles(...)` for role inference.
- Updates changed publication fields.
- Commits transaction and returns summary:
  - total publications,
  - enriched record count,
  - fields that were enriched.

Why it matters:
- Lets you improve publication quality after initial extraction.


## Nodes

### `nodes/__init__.py`
Empty package marker for node modules.


### `nodes/parser.py`
PDF text extraction and CV boundary detection node.

Main behavior:
- Reads PDF content using PyMuPDF (`fitz`).
- Supports both:
  - single PDF file input,
  - folder containing multiple PDFs.
- Splits CVs by blank-page separators.
- Produces `raw_texts` list of tuples:
  - `(candidate_label, cv_text)`

Key helper:
- `detect_cv_boundaries(pages)` groups contiguous non-empty pages into one CV block.

Why it matters:
- Converts uploaded PDF bytes into text units that downstream extraction can process per candidate.


### `nodes/llm_extractor.py`
Most complex backend component: extraction, normalization, fallback logic, and enrichment orchestration.

Core responsibilities:
- Loads `.env` to access LLM API key.
- Defines strict Pydantic extraction schema (`CVExtraction`) and nested models.
- Configures OpenRouter-backed `ChatOpenAI` client.
- Uses structured output extraction prompt for CV text.
- Cleans null-like strings and normalizes fields.
- Converts education values to `normalized_percentage`.
- Handles special school entries (`SSC/HSSC`) by moving institution to board when needed.
- Controls skill behavior:
  - If no explicit skills section exists, clears extracted skills.
  - Tries inference from roles/publication titles via LLM.
  - Falls back to deterministic keyword extraction from raw text.
- Runs publication enrichment and authorship inference after extraction.
- Applies retry with exponential backoff around LLM calls.
- Uses a heuristic non-LLM fallback extractor if structured extraction fails.

Important internal helpers:
- `clean_nulls`
- `normalize_education`
- `normalize_school_education_fields`
- `infer_skills_if_missing`
- `infer_skills_from_text`
- `heuristic_extract`
- `invoke_with_retries`

Why it matters:
- This is where unstructured CV text becomes structured, validated, and normalized domain data.


### `nodes/database_storage.py`
Persistence node: maps extracted dictionaries to SQLAlchemy models and stores records.

Main behavior:
- Skips processing if prior error exists or extraction is empty.
- Deduplicates by normalized candidate name.
- Creates new candidate with monotonic external id format (`cv_{id}`).
- Inserts related rows:
  - education
  - experience
  - skills
  - publications
  - books
  - patents
  - supervised students
- Sets `Skill.inferred` based on whether skills were explicit vs inferred.
- Commits successful batch; rolls back on exceptions.

Why it matters:
- Converts extracted payload into durable relational records.


## Services

### `services/__init__.py`
Empty package marker for service modules.


### `services/publication_enricher.py`
Reusable publication metadata and authorship enrichment logic.

Main behavior:
- Queries CrossRef by publication title.
- Uses token overlap guard to avoid weak/incorrect matches.
- Extracts metadata candidates:
  - DOI
  - publisher
  - ISSN
  - journal name
  - conference name
  - conference maturity
  - proceedings publisher
- Enriches only missing target fields (does not overwrite existing non-empty values).
- Replaces generic venue labels with enriched venue name when possible.
- Infers authorship role from author order and candidate-name matching.

Why it matters:
- Improves publication data quality and consistency after initial CV extraction.


## Migrations

### `migrations/versions/add_publication_crossref_fields.py`
SQL migration helper script.

What it does:
- Contains SQL statements to add CrossRef-related columns to `publications` table.
- Exposes helper `get_sql_statements()`.
- Prints SQL statements when run directly.

Important note:
- File explicitly says Alembic environment is not configured, so migration is currently manual/script-driven.


## Tests

### `tests/__init__.py`
Empty package marker for test package imports.


### `tests/test_llm_extractor_helpers.py`
Unit test for school education normalization helper.

What it verifies:
- `normalize_school_education_fields` moves board-like values from institution to board for SSC/HSSC.
- Non-school degrees keep institution untouched.


### `tests/test_publication_enricher.py`
Unit tests for publication enrichment and authorship logic.

What it verifies:
- CrossRef overlap guard picks relevant result and ignores unrelated candidates.
- Enrichment does not overwrite existing non-empty DOI/publisher values.
- Venue can be improved from generic label to actual journal name.
- Authorship role inference for first, corresponding, co-author, and first_and_corresponding cases.
- Existing weaker roles can be overridden when stronger evidence exists.


## Generated and Non-Source Folders

### `__pycache__/`
Python bytecode cache folder.

Why it is here:
- Automatically generated by Python runtime.
- Not part of source logic.


## External Backend Dependencies (Outside This Folder)

This backend imports a few modules from parent package directory:
- `talash/db_connect.py` for DB session and initialization.
- `talash/db_models.py` for SQLAlchemy ORM models and enums.

Even though they are outside `backend/`, they are core to runtime behavior.


## API Quick Reference

Base prefixes:
- `/api/cv`
- `/api/publications`

Main endpoints:
- `POST /api/cv/upload`
- `GET /api/cv/candidates`
- `GET /api/cv/candidates/{candidate_id}`
- `POST /api/publications/enrich/{candidate_id}`


## Operational Notes

- `OPENROUTER_API_KEY` must exist in project root `.env` for LLM extraction.
- Publication enrichment calls external CrossRef API and includes a contact email from `CROSSREF_CONTACT_EMAIL` or fallback default.
- Current CORS policy allows all origins, methods, and headers (good for dev, tighten for production).
- Migration flow is manual at the moment; consider adding Alembic for managed schema evolution.


## Suggested Future Improvements

- Add backend-specific run and test commands in this file once startup process is fully standardized.
- Add request/response examples for each endpoint.
- Add architecture diagram for parser -> extractor -> storage graph.
- Add stricter production CORS and environment profile guidance.
- Add Alembic migration framework and versioned schema lifecycle.
