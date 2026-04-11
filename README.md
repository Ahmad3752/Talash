# Talash — CV Extraction Pipeline

Talash is a small prototype pipeline to extract structured CV/resume data from PDF files and store the results in a PostgreSQL database. The project uses PDF parsers (PyMuPDF), an LLM-based extraction flow (LangGraph / LangChain adapters), and SQLAlchemy models to persist results.

Key features
- Extract CVs from single or batched PDF files
- Uses a structured LLM output schema (Pydantic) for validation
- Stores candidates, education, experience, publications, books, patents and supervised students in Postgres

Prerequisites
- Python 3.11+ (recommended)
- Docker & Docker Compose (for running Postgres locally)
- Git

Quickstart (development)

1. Start Postgres with Docker Compose

```sh
docker compose up -d
# or: docker-compose up -d
```

The repository includes a simple `docker-compose.yml` that creates a Postgres service named `talash_db` with credentials shown below.

2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv myvenv
& myvenv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Add environment variables

Create a `.env` file in the repository root and populate any required API keys (examples used in notebooks):

```
OPENROUTER_API_KEY=your_openrouter_key_here
```

5. Initialize the database schema

Run the helper that creates tables (uses DB settings found in `talash/db_connect.py`):

```bash
python -c "from talash.db_connect import init_db; init_db()"
```

6. Run the extraction pipeline (notebook)

The main interactive entry is the notebook at `talash/pr.ipynb`. Open it in VS Code or Jupyter and run the cells. Update the `pdf_path` in the notebook (see the "Cell 10 — Run" cell) to point at a PDF or folder of PDFs to process.

Notes about DB and credentials
- The included `docker-compose.yml` uses the following Postgres values:

```
POSTGRES_USER: talash
POSTGRES_PASSWORD: talash123
POSTGRES_DB: talash_db
```

When running Postgres via Docker Compose the container name is `talash_db`. You can check the DB with:

```bash
docker exec -it talash_db psql -U talash -d talash_db -c "\dt"
```

Files of interest
- Notebook: `talash/pr.ipynb` — end-to-end demo and cells to run/reset DB
- DB: `talash/db_connect.py`, `talash/db_models.py` — SQLAlchemy models and helpers

Git & repository notes
- This repo ignores local virtualenvs, the `Cvs/` folder (PDFs and outputs), and secrets via `.gitignore`.
- Before committing, make sure you do not include private keys or large PDF batches.

Contributing
- This project is a prototype. If you want to contribute, open an issue or a PR with focused changes (tests, docs, or small refactors).

License
- Add a license file if you plan to publish this repository (MIT is a simple option).

Troubleshooting
- If SQLAlchemy cannot connect, ensure Postgres is running and ports are mapped (`5432:5432`).
- If you see missing package errors, re-run `pip install -r requirements.txt` inside the activated virtualenv.

Enjoy! If you want, I can also:
- add a simple CLI runner script to invoke the pipeline outside the notebook
- create a GitHub Actions workflow to run tests / lint
