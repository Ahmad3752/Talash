# TALASH Milestone 1 Notes

## Section 1: Project Overview

### Full Project Title and Acronym
- **Project Title:** Talent Acquisition & Learning Automation for Smart Hiring
- **Acronym:** **TALASH**

### Problem Being Solved
Manual CV screening in recruitment workflows is slow, inconsistent, and difficult to scale. Traditional practices require recruiters to read many CVs line by line, which introduces several limitations:

- High time cost per candidate
- Human bias and inconsistency in evaluation
- Difficulty comparing candidates fairly across different CV formats
- Loss of potentially relevant details due to reviewer fatigue
- Limited traceability of how and why candidates were shortlisted

In university and academic hiring settings, this problem becomes more severe because CVs include complex, domain-specific sections (publications, supervision, patents, grants, teaching, and research profiles) that are hard to normalize manually.

### Proposed Solution
TALASH proposes an **LLM-based smart recruitment system** that automates CV ingestion, extraction, structuring, and downstream analysis. Instead of relying on manual reading, TALASH converts unstructured resumes into structured records and supports decision-making through standardized profiles and scoring-ready data.

Core solution idea:
- Ingest PDF/DOCX CVs
- Extract content using parser + LLM pipeline
- Convert outputs into strict structured JSON
- Validate and store in relational database
- Expose results through API and dashboard for recruiter review

### Target Domain
- **Primary target domain:** University/academic recruitment
- **Typical use cases:** Faculty hiring, research staff recruitment, and candidate shortlisting where educational and research credentials are critical.

### Course Context
- Developed as part of **CS417: Large Language Models**
- Milestone 1 demonstrates foundational system design and implemented preprocessing capabilities for an LLM-driven HR application.

---

## Section 2: Objectives and Scope

### Main Objective of TALASH
The main objective of TALASH is to build an end-to-end intelligent recruitment platform that automates candidate profile extraction and enables evidence-based, scalable hiring decisions using LLM-driven NLP pipelines.

### Functional Modules Planned for the Full System
The full TALASH system is planned as a modular architecture including:

1. CV Ingestion and File Monitoring Module
2. Preprocessing and Structured Extraction Module
3. Educational Profile Analysis Module
4. Research Profile Analysis Module
5. Professional Experience Analysis Module
6. Skills Intelligence and Classification Module
7. Candidate Scoring and Ranking Module
8. Missing Information Detection Module
9. AI Draft Email/Communication Module
10. Recruiter Dashboard and Analytics Module
11. Export and Reporting Module (CSV/Excel/PDF summaries)
12. Audit, Logging, and Traceability Module

### Milestone 1 In-Scope Modules
Milestone 1 focuses on design + foundation implementation. Scope includes:

- **Preprocessing Module (COMPLETED)**
- System Architecture Design
- LLM/NLP Pipeline Design
- Database/Storage Design
- UI/UX Wireframes
- Early Prototype with basic upload/read flow

This scope establishes data readiness and technical scaffolding required for analytic and ranking modules in Milestone 2 and 3.

---

## Section 3: Tech Stack

This section documents selected technologies and the rationale behind each choice.

### Frontend

| Component | Technology | Reason for Choice |
|---|---|---|
| Framework | React.js | Component-based architecture, fast UI development, strong ecosystem, suitable for dynamic dashboards |
| Styling | Tailwind CSS | Rapid utility-first styling, consistent design system, easy responsive implementation |
| Charts/Graphs | Recharts or Chart.js | Clear comparative visualizations for candidate metrics and ranking insights |
| HTTP Client | Axios | Reliable promise-based API communication with backend endpoints |

### Backend

| Component | Technology | Reason for Choice |
|---|---|---|
| Framework | FastAPI (Python) | Native async support, automatic API documentation, high performance, ideal for ML/LLM pipelines |

### LLM Integration

| Component | Technology | Reason for Choice |
|---|---|---|
| Primary LLM | GPT-4o via OpenAI API | Strong structured extraction quality and robust reasoning on noisy CV text |
| Fallback/Alternative | Claude 3.5 Sonnet via Anthropic API | Resilience via provider redundancy and alternative extraction behavior |
| Prompt Strategy | Structured JSON extraction prompts | Enforces machine-readable outputs and minimizes parser ambiguity |
| Orchestration | LangChain | Prompt templating, model abstraction, and easy pipeline composition |

### PDF Parsing / Preprocessing

| Tool | Use in TALASH |
|---|---|
| pdfplumber | Primary text extraction from structured PDFs |
| PyMuPDF (fitz) | Layout-aware fallback extraction for difficult formatting |
| pdfminer.six | Additional fallback for complex or parser-resistant files |
| python-docx | Future support for DOCX CV ingestion |

### Data Storage

| Component | Technology | Reason for Choice |
|---|---|---|
| Relational DB | PostgreSQL | Reliable ACID transactions, relational integrity, scalable structured storage |
| ORM | SQLAlchemy | Clean Pythonic DB layer, schema mapping, migration-friendly modeling |
| Export | pandas + openpyxl | Practical data processing and multi-sheet Excel report generation |

### File Management

| Component | Technology | Reason for Choice |
|---|---|---|
| Ingestion Pattern | Folder-based CV ingestion | Supports single and batch processing workflows |
| Folder Monitoring | Watchdog | Event-driven automatic pipeline triggering on new uploads |

### Deployment and Collaboration

| Component | Technology | Reason for Choice |
|---|---|---|
| Containerization | Docker | Reproducible runtime environment and easy local setup |
| Version Control | GitHub | Collaborative development, version tracking, milestone management |

---

## Section 4: System Architecture

TALASH follows a layered architecture to separate concerns and support maintainability.

### Layer 1: Presentation Layer (React Frontend)
- CV Upload Interface
- Candidate Dashboard
- Candidate Detail View
- Email Draft Viewer

### Layer 2: API Layer (FastAPI Backend)
- CV ingestion endpoint
- Analysis trigger endpoint
- Results retrieval endpoint
- Email generation endpoint

### Layer 3: LLM Processing Layer
- PDF Parser
- LLM Extraction Engine
- Analysis Modules (Education, Research, Experience, Skills)
- Summary Generator

### Layer 4: Data Layer
- PostgreSQL Database
- File storage for uploaded CVs
- CSV/Excel export engine

### Cross-Layer Data Flow
**CV Upload -> Folder Monitor -> PDF Parser -> LLM Extraction -> Structured JSON -> Database Storage -> API -> Frontend Dashboard**

Interaction summary:
1. User uploads CV(s) through frontend.
2. Backend stores files and signals processing.
3. Parser extracts raw text.
4. LLM transforms text into structured schema-aligned JSON.
5. Validation and post-processing clean the output.
6. Data persisted in PostgreSQL and optional Excel output generated.
7. API serves candidate records and processing status to frontend dashboard.

---

## Section 5: Preprocessing Module (Completed - Most Detailed)

### 5.1 Purpose
The preprocessing module is the completed core of Milestone 1. Its purpose is to convert unstructured CV documents into normalized, machine-readable data that downstream modules can directly consume.

Primary goals:
- Convert unstructured PDF CVs to structured records
- Extract heterogeneous academic/professional fields reliably
- Produce tabular outputs for storage, analytics, and reporting
- Build the foundation for ranking and recommendation modules

### 5.2 Input
- Input source: PDF CV files uploaded into a designated ingestion folder
- Trigger mechanism: Watchdog monitors folder and triggers pipeline on new file creation
- Processing mode: Supports both single CV and batch CV workflows
- Input variability considered: Different templates, mixed formatting, and variable section ordering

### 5.3 Extraction Fields and Structured Tables

#### Table 1: Personal Information

| Field | Description |
|---|---|
| name | Candidate full name |
| email | Primary email address |
| phone | Contact number |
| address | Current or stated location/address |
| LinkedIn | LinkedIn profile URL |
| GitHub | GitHub profile URL |
| website | Personal website/portfolio link |

#### Table 2: Education

| Field | Description |
|---|---|
| degree_title | Degree name (e.g., BS, MS, PhD) |
| specialization | Major/specialization area |
| institution | University/college/school name |
| start_year | Program start year |
| end_year | Program completion year |
| marks_cgpa | Raw grade value extracted from CV |
| scale | Grading scale (e.g., 4.0, 10.0, 100) |
| percentage_equivalent | Normalized percentage |
| board_name | Board/university authority if applicable |
| level | SSE/HSSC/UG/PG/PhD |

#### Table 3: Experience

| Field | Description |
|---|---|
| job_title | Job position/title |
| organization | Employer/organization name |
| start_date | Job start date |
| end_date | Job end date |
| employment_type | Full-time/Part-time/Contract/Internship etc. |
| description | Role responsibilities/achievements |
| is_current | Whether role is currently active |

#### Table 4: Skills

| Field | Description |
|---|---|
| skill_name | Extracted skill term |
| category | technical/soft/domain |
| source_section | Section where skill was detected |

#### Table 5: Publications

| Field | Description |
|---|---|
| title | Publication title |
| authors | Author list |
| venue_name | Journal/conference name |
| venue_type | journal/conference |
| year | Publication year |
| doi | DOI identifier |
| candidate_author_position | Candidate's author order |
| is_first_author | First-author flag |
| is_corresponding_author | Corresponding-author flag |

#### Table 6: Supervision

| Field | Description |
|---|---|
| student_name | Supervised student name |
| degree_level | MS/PhD |
| role | main/co |
| year_start | Supervision start year |
| year_end | Supervision end year |
| thesis_title | Thesis/dissertation title |

#### Table 7: Patents

| Field | Description |
|---|---|
| patent_number | Patent identifier |
| title | Patent title |
| date | Patent date |
| inventors | Inventor list |
| country | Filing country |
| verification_link | URL/reference for verification |

#### Table 8: Books

| Field | Description |
|---|---|
| book_title | Title of book |
| authors | Author list |
| isbn | ISBN code |
| publisher | Publishing house |
| year | Publication year |
| online_link | URL for online reference |

### 5.4 LLM Prompt Strategy for Extraction
The extraction step uses a structured prompt sent to GPT-4o. Prompt design emphasizes deterministic, schema-compatible output for automated parsing.

Prompt components:
- **Role instruction:** "You are an expert CV parser."
- **Output constraint:** Return **strict JSON only** (no prose, no markdown).
- **Schema directives:** Field-by-field definitions to reduce ambiguity.
- **Missing value policy:** Return `null` when data is unavailable; do not infer or hallucinate values.
- **Normalization hints:** Standardized formats for date and grade outputs.

This strategy is designed to maximize machine-readability and minimize manual correction effort.

### 5.5 Post-Processing
After LLM output is received, TALASH applies a deterministic post-processing pipeline:

1. JSON validation and schema enforcement with Pydantic models
2. CGPA normalization:
   - Convert values like 3.5/4.0 to percentage
   - Convert values like 8.5/10 to percentage
3. Date standardization to `YYYY-MM` format where possible
4. Null-handling policy:
   - Missing fields remain `null`
   - No fabricated replacements
5. Excel export via openpyxl:
   - One worksheet per relational table
   - Column-consistent and analysis-ready sheets

### 5.6 Output
Module outputs are produced in structured forms suitable for immediate downstream use:

- Multi-sheet Excel file containing extracted entities
- One sheet per conceptual table (personal, education, experience, etc.)
- Clean machine-readable format for database ingestion and analytics

### 5.7 Challenges Faced
Key implementation challenges in the completed preprocessing module:

- High variation in PDF templates and section ordering
- Inconsistent date expressions (e.g., month-year vs year-only)
- Diverse CGPA/marks scales across institutions
- Missing or partially specified profile fields
- Multi-column layouts that reduce parser coherence

Mitigation strategies included parser fallbacks, schema validation, normalization rules, and strict null policies.

---

## Section 6: LLM Pipeline Design

The full Milestone 1 extraction pipeline is defined as follows:

### Step 1: CV File Detection
- Watchdog monitors designated upload folder
- New PDF detection triggers processing automatically

### Step 2: Text Extraction
- pdfplumber used for primary extraction
- PyMuPDF used as fallback for difficult layouts
- Text cleaning stage removes extra whitespace and fixes encoding artifacts

### Step 3: Chunking (Long CV Handling)
- If token limit risk is detected, CV is segmented into logical blocks
- Typical sections: Education, Experience, Publications, Skills, and Others

### Step 4: LLM Extraction
- Clean text sent to GPT-4o with schema-constrained extraction prompt
- Model returns JSON containing all target fields
- LangChain manages prompt templates, model invocation, and response handling

### Step 5: Validation
- Pydantic models validate response shape and field types
- Missing mandatory values are flagged
- Type mismatches are corrected or logged for review

### Step 6: Storage
- Validated records stored in PostgreSQL via SQLAlchemy
- Excel export generated through openpyxl
- Original CV file retained with candidate ID reference

### Step 7: Status Update
- API returns processing status to frontend
- Candidate appears in dashboard when extraction completes

---

## Section 7: Database Design

TALASH uses a relational schema centered on a `candidates` parent table.

### Core Tables and Relationships

| Table | Key Fields | Relationship |
|---|---|---|
| candidates | id, name, email, cv_file_path, created_at, status | Parent entity |
| education | id, candidate_id, degree fields | Many-to-one to candidates via candidate_id |
| experience | id, candidate_id, experience fields | Many-to-one to candidates via candidate_id |
| skills | id, candidate_id, skill fields | Many-to-one to candidates via candidate_id |
| publications | id, candidate_id, publication fields | Many-to-one to candidates via candidate_id |
| supervision | id, candidate_id, supervision fields | Many-to-one to candidates via candidate_id |
| patents | id, candidate_id, patent fields | Many-to-one to candidates via candidate_id |
| books | id, candidate_id, book fields | Many-to-one to candidates via candidate_id |

### Integrity Design
- Each child table stores `candidate_id` foreign key referencing `candidates.id`
- This ensures normalized data, minimal redundancy, and traceability from any extracted record back to the source candidate
- Supports future joins for score computation and dashboard aggregation queries

---

## Section 8: UI/UX Design (Wireframes)

Milestone 1 includes conceptual wireframes and interaction planning for three core screens.

### Screen 1: CV Upload Page
- Drag-and-drop upload zone for PDFs
- Folder path input for batch processing
- Upload progress indicator
- Uploaded CV list with statuses: processing / done / error

### Screen 2: Candidate Dashboard
- Tabular candidate listing
- Columns:
  - Name
  - Education Score
  - Research Score
  - Experience Score
  - Overall Score
  - Actions
- Comparative bar chart for top candidates
- Filtering and sorting controls for recruiter workflow

### Screen 3: Candidate Detail Page
- Header: name, email, image placeholder
- Tab navigation:
  - Education
  - Research
  - Experience
  - Skills
  - Summary
- Each tab displays structured extracted data
- Summary tab includes AI-generated profile summary
- Missing information flag section
- Draft email button to request missing details

---

## Section 9: Early Prototype

### Implemented Features (Milestone 1)
- Basic React frontend with CV upload interface
- FastAPI backend with upload endpoint flow
- PDF extraction integration (including parser-based text extraction)
- Initial LLM extraction call to GPT-4o returning raw structured JSON
- Initial Excel export pipeline working for small batches (1-2 CVs)
- GitHub repository with organized frontend/backend structure

### Prototype Status Summary
The early prototype validates end-to-end feasibility of the TALASH concept:

- Input ingestion works
- Structured extraction path works
- Data can be exported and persisted
- UI and API skeleton are in place for extension in Milestones 2 and 3

---

## Section 10: Milestone 1 Evaluation Mapping

### Rubric Mapping Table

| Criterion | Marks | Coverage in Notes |
|---|---:|---|
| Criterion 1: System architecture and technical design | 4 | Section 4 and Section 7 |
| Criterion 2: UI/UX wireframes and design thinking | 4 | Section 8 |
| Criterion 3: Completed Preprocessing Module and Early Prototype | 12 | Section 5 and Section 9 |
| Criterion 4: Running demo | 5 | Demo plan below |

### Running Demo Plan (Criterion 4)
The live demo should show:

1. Uploading one or more CV PDFs
2. Automatic detection and pipeline trigger
3. Extraction completion and candidate entry visibility
4. Structured output preview (JSON/Excel/database record)
5. Frontend dashboard view of processed candidate(s)

---

## Section 11: Challenges and Decisions

### Why FastAPI over Django/Flask
- Better out-of-the-box async performance for I/O-heavy pipeline stages
- Automatic OpenAPI docs accelerate backend testing and integration
- Lightweight and modular design suits microservice-like LLM workflows

### Why GPT-4o over Open-Source Models
- Higher reliability for schema-following structured extraction
- Better robustness on noisy, heterogeneous CV text
- Reduced engineering overhead for prompt tuning in early milestones

### Why pdfplumber as Primary Parser
- Strong baseline extraction quality for many structured academic CV formats
- Straightforward integration in Python pipeline
- Works effectively with fallback strategy for edge cases

### Why PostgreSQL over MongoDB
- Structured relational schema aligns with normalized candidate entities
- Strong constraints and foreign keys improve data integrity
- Better fit for joins used in scoring, ranking, and analytics dashboards

### Key Design Decisions in Milestone 1
- Prioritize preprocessing before analysis modules to secure data quality
- Use strict JSON contracts + Pydantic validation to reduce downstream errors
- Separate parsing, extraction, validation, and storage as independent stages
- Design frontend early to guide API contracts and user flow

---

## Section 12: Future Work (Milestone 2 and 3 Preview)

Planned next-stage modules:

- Educational Profile Analysis module
- Research Profile Analysis module
- Professional Experience Analysis module
- Full interactive dashboard with richer graphs and filters
- Candidate scoring and ranking engine

Additional likely enhancements:
- Explainable scoring outputs for recruiter transparency
- Improved fallback model routing and retry policies
- Human-in-the-loop correction interface for extraction edits
- Automated email generation for shortlisting and missing info requests

---

## Suggested Report-Writing Use of These Notes

For formal LaTeX report drafting, this file can be directly mapped as:

- Introduction/Problem Statement: Section 1
- Objectives and Scope: Section 2
- Methodology/Implementation Design: Sections 3, 4, 6, 7
- Completed Work: Section 5 and Section 9
- Evaluation Alignment: Section 10
- Design Rationale and Limitations: Section 11
- Future Work and Conclusion Direction: Section 12

This structure supports a strong academic narrative from motivation -> design -> implementation -> evaluation mapping -> future direction.