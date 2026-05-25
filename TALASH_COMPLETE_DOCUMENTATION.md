# TALASH: Comprehensive Technical Documentation
## Talent Acquisition & Learning Automation for Smart Hiring

**Project Type:** Full-Stack Web Application (LLM-Powered CV Processing & Candidate Evaluation)  
**Course:** CS417 - Large Language Models  
**Semester:** Fall 2024  
**Institution:** [University Name]  
**Status:** Fully Functional Implementation  

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Objectives and Scope](#2-objectives-and-scope)
3. [Tech Stack](#3-tech-stack)
4. [System Architecture](#4-system-architecture)
5. [Functional Modules](#5-functional-modules)
6. [Web Application Features](#6-web-application-features)
7. [Database & Data Schema](#7-database--data-schema)
8. [LLM Prompting Strategy](#8-llm-prompting-strategy)
9. [Challenges Faced and Solutions](#9-challenges-faced-and-solutions)
10. [Results and Sample Outputs](#10-results-and-sample-outputs)
11. [Limitations](#11-limitations)
12. [Future Work](#12-future-work)

---

## 1. Project Overview

### 1.1 Problem Statement

Traditional CV screening and evaluation for faculty recruitment at universities involves severe bottlenecks:

- **Manual Labor Intensive**: Human reviewers must manually parse CVs, extract key information, and evaluate candidates across multiple dimensions
- **Inconsistent Assessment**: Different reviewers apply subjective criteria, leading to biased and inconsistent candidate rankings
- **Lack of Standardization**: CVs vary dramatically in format, completeness, and structure, making it impossible to apply uniform evaluation metrics
- **Scalability Issues**: Universities receive hundreds or thousands of applications; manual processing becomes impractical for large batches
- **Incomplete Information Capture**: Important metrics (publication quality, institutional prestige, research diversity, skill-role alignment) are often overlooked in traditional reviews
- **Time-to-Hire Delays**: Extended evaluation periods delay hiring decisions and allow top candidates to accept offers elsewhere

### 1.2 Proposed Solution: TALASH

TALASH (Talent Acquisition & Learning Automation for Smart Hiring) is an AI-powered, full-stack web application that:

- **Automatically parses CVs** from PDF uploads, identifying and separating multiple CVs in batch documents using heuristic boundary detection
- **Extracts structured data** from unstructured CV text using LLM-based extraction with Pydantic schema validation
- **Scores candidates multi-dimensionally** across six specialized evaluation modules (education, research, professional experience, skills, topic variability, collaboration)
- **Integrates external datasets** including QS World University Rankings, Scimago Journal Rankings, Web of Science indexing, CORE conference rankings, and publication APIs (CrossRef, OpenAlex)
- **Generates comprehensive reports** with visual dashboards, tabular comparisons, and AI-generated recommendations
- **Detects and flags missing information** with intelligent email draft generation for follow-up inquiries
- **Enables comparative analysis** with side-by-side candidate comparison and ranking views

### 1.3 Target Use Case: University Faculty Recruitment

TALASH is specifically designed for **faculty hiring at academic institutions**, where evaluation criteria emphasize:
- **Educational qualifications** (highest degree, institutional prestige, academic performance)
- **Research output and impact** (publication count, journal quality, conference participation, citation potential)
- **Student supervision capability** (MS and PhD students mentored)
- **Collaboration patterns** (co-author networks, interdisciplinary work)
- **Teaching-relevant skills** (domain expertise, professional experience)

The system accelerates faculty recruitment by:
1. Processing hundreds of applications in hours instead of weeks
2. Providing standardized, objective scoring across all dimensions
3. Surfacing qualified candidates who might be missed in manual screening
4. Generating evidence-backed recommendations for hiring committees

---

## 2. Objectives and Scope

### 2.1 System Objectives

1. **Automated CV Processing**: Parse PDF CVs, extract structured candidate data, and store in normalized database
2. **Intelligent Data Extraction**: Use LLM with structured schema to reliably extract personal info, education, experience, publications, patents, and supervision records
3. **Multi-Dimensional Scoring**: Evaluate candidates across six specialized scoring modules with documented justifications
4. **Research Quality Assessment**: Integrate external datasets to determine publication quality (journal quartiles, conference rankings, indexing status)
5. **Skill-Job Alignment Analysis**: Match candidate skills with job requirements and track alignment evidence
6. **Comprehensive Reporting**: Generate detailed candidate profiles with visualizations, comparative rankings, and actionable recommendations
7. **Missing Information Detection**: Automatically identify incomplete data and draft personalized emails for follow-up
8. **Scalability**: Handle batch uploads of 50-500+ CVs with background processing and live status updates
9. **Data Integrity**: Prevent duplicate processing via fingerprinting; ensure data consistency across extractions and scoring
10. **User-Friendly Interface**: Provide intuitive web UI for upload, browsing, and comparing candidates

### 2.2 Scope Boundaries

#### **Included in TALASH**
- PDF CV parsing and text extraction
- Structured data extraction (education, experience, skills, publications, patents, supervision)
- Educational profile scoring (degree level, GPA, institution prestige)
- Research performance scoring (publication quality, authorship analysis, supervision record)
- Professional experience and skill alignment scoring
- Topic variability and co-author collaboration analysis
- Multi-candidate batch processing
- Web UI for upload, browsing, and detailed candidate views
- Comparative ranking dashboard
- Email notification system for missing information
- Redis caching for CV deduplication
- Database persistence (SQLite or PostgreSQL)

#### **Explicitly NOT Included**
- Interview scheduling or HR workflow integration
- Job description parsing or matching (job criteria are hardcoded assumptions)
- Cover letter or personal statement analysis
- Credit checking or background verification
- Portfolio or website analysis
- Real-time API integrations with academic databases (uses cached CSV datasets)
- Automated offer generation or contract templates
- Multi-language support (English-only)
- Role-based access control or user management (single-user assumption)
- Compliance with GDPR, CCPA, or other data privacy regulations
- LLM fine-tuning or custom model training

---

## 3. Tech Stack

### 3.1 Frontend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | React | 19.2.5 | UI component library with hooks-based architecture |
| **Build Tool** | Vite | 8.0.10 | Modern, fast build system with HMR support |
| **Routing** | React Router DOM | 7.14.2 | Client-side routing for multi-page SPA |
| **Styling** | Tailwind CSS | 4.2.4 | Utility-first CSS framework for responsive design |
| **Charting** | Recharts | 3.8.1 | React charting library for score visualizations and progress bars |
| **Icons** | Lucide React | 1.14.0 | SVG icon set for UI components |
| **HTTP Client** | Axios | 1.15.2 | Promise-based HTTP client for API communication |
| **Notifications** | React Hot Toast | 2.6.0 | Toast notifications for feedback (upload, processing, errors) |
| **CSS Processing** | PostCSS + Autoprefixer | 8.5.13 + 10.5.0 | CSS vendor prefixing and modern syntax support |
| **Linting** | ESLint | 10.2.1 | JavaScript code quality and style checking |

**Frontend Features:**
- **Upload Page**: Drag-and-drop PDF upload with batch processing
- **Candidates Page**: Tabular view of all processed candidates with filters and sorting
- **Candidate Detail Page**: Comprehensive profile with education, experience, publications, scores, and recommendations
- **Rankings Page**: Comparative ranking view with configurable weights
- **Dark/Light Theme Toggle**: CSS variables-based theme switching
- **Live Processing Updates**: Real-time status indicators during batch processing
- **Responsive Design**: Mobile-compatible UI with flexible layouts

### 3.2 Backend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | FastAPI | Latest | Modern, async Python web framework with automatic OpenAPI docs |
| **Server** | Uvicorn | Latest | ASGI server for async application handling |
| **Async Runtime** | AsyncIO | Python 3.11+ | Python's native async/await concurrency |
| **Database ORM** | SQLAlchemy | Latest | SQL toolkit and ORM for database abstraction |
| **Validation** | Pydantic | v2 | Data validation and serialization with JSON schema support |
| **HTTP Client** | AIOHTTP | 3.13.4 | Async HTTP client for external API calls |
| **PDF Processing** | PyMuPDF (fitz) | Latest | Robust PDF text extraction and page parsing |
| **Data Processing** | Pandas | Latest | DataFrame operations for CSV/dataset handling |
| **Caching** | Redis | 7 (Docker) | In-memory cache for CV deduplication and session state |
| **Database** | PostgreSQL 15 (Docker) | 15 | Production relational database with JSONB support |
| **Environment** | Python-Dotenv | Latest | Environment variable management |

**Backend Features:**
- **REST API**: RESTful endpoints for CV upload, processing, retrieval, and candidate management
- **Background Processing**: LangGraph-based workflow with async CV processing queue
- **Database Session Management**: SQLAlchemy session pooling for concurrent requests
- **CORS Middleware**: Cross-origin request support for frontend integration
- **Error Handling**: Comprehensive exception handling with detailed error messages
- **Logging**: Detailed logging for debugging and monitoring

### 3.3 LLM Integration

| Component | Service | Model | Purpose |
|-----------|---------|-------|---------|
| **Primary LLM Provider** | Groq | llama-3.3-70b-versatile | CV extraction, fast inference, free tier |
| **Secondary LLM Provider** | Google | gemini-2.0-flash | Fallback for structured extraction (replaced gemini-1.5-flash) |
| **Tertiary LLM Provider** | OpenRouter | openai/gpt-4o-mini or /auto | Final fallback, structured calls with gpt-4o |
| **LLM Framework** | LangChain | 0.1+ | Structured output handling, LLM orchestration |
| **LLM Routing** | litellm | Latest | Provider abstraction, multi-key rotation, fallback logic |
| **Async Support** | LangChain Core | Latest | Async message types and LLM calls |

**LLM Capabilities Used:**
- Structured JSON extraction with Pydantic schema enforcement
- Multi-turn conversation for clarification (not currently used)
- Zero-shot prompting with detailed extraction instructions
- Temperature control (0.7) for consistent, deterministic outputs

### 3.4 External Data Sources & APIs

| Data Source | Format | Usage | Update Frequency |
|------------|--------|-------|------------------|
| **QS World University Rankings 2025** | CSV | Institution prestige scoring for education quality | Annual (cached) |
| **Scimago Journal Rankings 2025** | CSV (sep=';') | Journal quartile lookup by ISSN | Annual (cached) |
| **CORE Portal Conferences** | CSV | Conference ranking lookup (A*, A, B, C tiers) | Quarterly (cached) |
| **CrossRef API** | REST API | Publication metadata recovery (title→DOI→ISSN) | Real-time |
| **OpenAlex API** | REST API | Fallback publication metadata, citation counts | Real-time |
| **Web of Science Database** | CSV | WoS journal indexing status | Cached dataset |

### 3.5 Deployment & Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Containerization** | Docker | Container images for consistent deployment |
| **Orchestration** | Docker Compose | Multi-container application (DB, Redis, Backend, Frontend) |
| **File Storage** | Local filesystem (temp) | Temporary CV PDF storage during processing |
| **Environment Config** | .env file | API keys, database URLs, SMTP credentials |

---

## 4. System Architecture

### 4.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (React/Vite)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │  Upload Page │  │  Candidates  │  │  Candidate   │  Rankings    │
│  │              │  │    List      │  │   Detail     │  View        │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
│          ▲                 ▲                ▲             ▲           │
└──────────┼─────────────────┼────────────────┼─────────────┼───────────┘
           │                 │                │             │
        POST /upload      GET /candidates  GET /candidates GET /rankings
        GET /status      GET /candidates/:id    
           │                 │                │             │
┌──────────┼─────────────────┼────────────────┼─────────────┼───────────┐
│  BACKEND (FastAPI + Async)│                │             │           │
│          │                 │                │             │           │
│  ┌───────▼────────────────────────────────────────────────┐           │
│  │            PDF Upload & Validation                     │           │
│  │  • Temp file storage, file size validation            │           │
│  │  • Automatic file cleanup after processing            │           │
│  └───────┬────────────────────────────────────────────────┘           │
│          │                                                            │
│  ┌───────▼────────────────────────────────────────────────┐           │
│  │     CV Boundary Detection & Fingerprinting            │           │
│  │  • Heuristic: email/phone/CV keyword detection        │           │
│  │  • SHA-256 fingerprinting for deduplication           │           │
│  │  • Multi-CV splitting (e.g., 3 CVs in 1 PDF)        │           │
│  │  • Redis cache: check if CV already processed         │           │
│  └───────┬────────────────────────────────────────────────┘           │
│          │                                                            │
│  ┌───────▼────────────────────────────────────────────────┐           │
│  │     Async Processing Queue (asyncio.Queue)            │           │
│  │  • Single worker thread for sequential processing     │           │
│  │  • Live status updates visible to frontend            │           │
│  │  • Error handling per CV (continues on failure)       │           │
│  └───────┬────────────────────────────────────────────────┘           │
│          │                                                            │
│  ┌───────▼────────────────────────────────────────────────┐           │
│  │     LangGraph CV Processing Pipeline (runner.py)      │           │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐   │           │
│  │  │LLM Extrac-   │  │Database      │  │Scoring     │   │           │
│  │  │tion (GPT-4o) │→ │Storage       │→ │Nodes       │   │           │
│  │  │(Pydantic)    │  │              │  │            │   │           │
│  │  └──────────────┘  └──────────────┘  └────────────┘   │           │
│  │         │                                    │          │           │
│  │         ▼                                    ▼          │           │
│  │   CVExtraction Schema              Scoring Results    │           │
│  │  (personal_info, education,        (education_score,  │           │
│  │   experience, skills,               research_score,   │           │
│  │   publications, books,              experience_score) │           │
│  │   patents, supervision)                               │           │
│  └───────────────────────────────────────────────────────┘           │
│          │                                                            │
│  ┌───────▼────────────────────────────────────────────────┐           │
│  │         Database Storage (SQLAlchemy ORM)             │           │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐   │           │
│  │  │Candidates    │  │Publications  │  │Education   │   │           │
│  │  │Experience    │  │Books/Patents │  │Skills      │   │           │
│  │  │Supervision   │  │Scores        │  │Summary     │   │           │
│  │  └──────────────┘  └──────────────┘  └────────────┘   │           │
│  └───────────────────────────────────────────────────────┘           │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│              EXTERNAL SERVICES & DATA SOURCES                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐   │
│  │ Groq API         │  │ Google Gemini    │  │ OpenRouter     │   │
│  │ (Primary LLM)    │  │ (Fallback LLM)   │  │ (Last Resort)  │   │
│  └──────────────────┘  └──────────────────┘  └────────────────┘   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐   │
│  │ CrossRef API     │  │ OpenAlex API     │  │ QS Rankings    │   │
│  │ (Publication     │  │ (Publication     │  │ (Cached CSV)   │   │
│  │  metadata)       │  │  metadata)       │  │                │   │
│  └──────────────────┘  └──────────────────┘  └────────────────┘   │
│  ┌──────────────────┐  ┌──────────────────┐                        │
│  │ Scimago 2025     │  │ CORE Conferences │                        │
│  │ (Cached CSV)     │  │ (Cached CSV)     │                        │
│  └──────────────────┘  └──────────────────┘                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│         STORAGE LAYER (Docker Containers)                          │
│  ┌──────────────────────┐  ┌──────────────────────┐               │
│  │ PostgreSQL 15        │  │ Redis 7 Alpine       │               │
│  │ (Relational Data)    │  │ (Cache & Session)    │               │
│  └──────────────────────┘  └──────────────────────┘               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Data Flow: CV Upload to Candidate Report

```
1. USER UPLOADS PDF
   ↓
2. FASTAPI /upload ENDPOINT
   • Validates file (PDF only, size limit)
   • Stores temp file
   • Extracts text using PyMuPDF
   • Calls detect_cv_boundaries()
   ↓
3. CV BOUNDARY DETECTION
   • Splits multi-CV PDF into individual CVs
   • Uses heuristic: email/phone/keyword detection
   • Creates fingerprint (SHA-256) for each CV
   ↓
4. REDIS DEDUPLICATION CHECK
   • Check if CV fingerprint exists in cache
   • If exists: skip processing, return cached results
   • If new: continue to LLM extraction
   ↓
5. ENQUEUE FOR PROCESSING
   • Add CV to asyncio.Queue
   • Assign upload_id and CV sequence (e.g., CV 2 of 5)
   • Frontend polls GET /live-updates for progress
   ↓
6. LLM CV EXTRACTION (runner.py LangGraph)
   • Call LLM with extraction prompt + CV text
   • LLM returns JSON (CVExtraction schema with Pydantic validation)
   • Parse: personal_info, education, experience, skills, publications, patents, supervision
   ↓
7. DATABASE STORAGE
   • Save Candidate record (name, email, phone)
   • Save Education records (degree, institution, GPA, years)
   • Save Experience records (job titles, companies, dates)
   • Save Skill records (extracted or inferred)
   • Save Publication records (title, venue, year, authorship role)
   • Save Book and Patent records
   • Save SupervisedStudent records
   ↓
8. TRIGGER SCORING PIPELINE
   • Education Analysis: degree level, GPA, institution prestige
   • Research Analysis: publication quality, journal rankings, authorship analysis
   • Experience & Skill Analysis: role progression, skill alignment
   • Topic Variability & Co-author Analysis: research diversity, collaboration patterns
   ↓
9. SAVE SCORE RECORDS
   • Insert EducationScore, ResearchScore, ProfessionalExperienceScore, etc.
   • Compute overall score as weighted average
   ↓
10. GENERATE SUMMARY
    • Compile CV summary with key findings
    • Identify missing information
    • Generate recommendations
    • Create email draft for follow-up (if needed)
    ↓
11. CACHE FINGERPRINT
    • Write CV fingerprint to Redis
    • Link fingerprint → candidate_id for future uploads
    ↓
12. UPDATE FRONTEND
    • /live-updates returns: status=completed, candidate details
    • Frontend redirects to /candidates/:id
    ↓
13. USER VIEWS RESULTS
    • Candidate Detail Page shows all extracted data
    • Scores displayed with visualizations and justifications
    • Recommendations and missing information visible
```

### 4.3 Component Interactions

**Frontend ↔ Backend Communication:**
- **POST /upload**: Upload PDF file, receive upload_id
- **GET /live-updates?upload_id=X**: Poll for processing status (cv_num, total_cvs, status)
- **GET /candidates**: Fetch all candidates with basic info
- **GET /candidates/:id**: Fetch detailed candidate profile with all scores
- **GET /recommendations**: Get missing info and email draft for a candidate

**Backend Internal Flow:**
1. **PDF Upload** → PyMuPDF text extraction
2. **CV Boundary Detection** → Multiple CVs split
3. **Deduplication Check** → Redis fingerprint lookup
4. **Queue Enqueue** → asyncio.Queue
5. **Worker Processing** → LangGraph execution
6. **LLM Extraction** → Structured schema output
7. **Database Persist** → SQLAlchemy ORM
8. **Scoring Nodes** → edu_scores.py, research_scores.py, etc.
9. **Report Generation** → summarizers.py
10. **Frontend Fetch** → REST API endpoints

---

## 5. Functional Modules

TALASH implements a comprehensive multi-module evaluation system with distinct responsibilities:

### 5.1 Module 1: Preprocessing & PDF Ingestion

**Responsibility**: Extract CV text from PDF files and detect multiple CVs in single documents.

**Implementation Approach:**
- Uses **PyMuPDF (fitz)** for robust PDF text extraction across pages
- Implements **heuristic boundary detection** to identify CV starts using:
  - Email pattern matching: `\b[\w.+\-]+@[\w\-]+\.[a-z]{2,}\b`
  - Phone pattern matching: `(\+?\d[\d\s\-\(\)]{7,}\d)`
  - CV keyword matching: "curriculum vitae", "resume", "biodata"
  - Name label detection: `^name\s*[:\-]`
- **Boundary logic**: A new CV is detected if the page contains email/phone AND cv_keyword, or name label AND email
- **Deduplication**: SHA-256 fingerprinting of the first 1000 characters; fingerprints stored in Redis
- **Batch handling**: Supports extracting 3-10+ CVs from single multi-page PDFs

**Input**: PDF file (binary)
**Output**: List of CV text strings, each with unique fingerprint

**Error Handling:**
- Corrupted PDFs: PyMuPDF returns empty text; module logs and continues
- Multi-page extraction failures: Page-level errors don't crash pipeline; continues with remaining pages
- Empty CVs: Filters out CV text < 200 characters

### 5.2 Module 2: Structured Data Extraction

**Responsibility**: Parse CV text using LLM to extract structured candidate information into normalized fields.

**Implementation Approach:**
- **LLM Provider**: Groq (llama-3.3-70b-versatile) with fallback to Gemini and OpenRouter
- **Schema**: Pydantic model `CVExtraction` with 8 nested classes:
  - `PersonalInfo`: name, email, phone
  - `DegreeRecord`: degree, field, institution, start_year, end_year, cgpa, cgpa_scale, percentage, board
  - `ExperienceRecord`: company, role, employment_type, start_date, end_date, description
  - `Publication`: type (journal/conference), title, venue, issn, year, authors, authorship_role, wos_indexed, scopus_indexed, quartile, impact_factor, core_rank
  - `Book`: title, authors, isbn, publisher, year, url, authorship_role
  - `Patent`: patent_number, title, year, inventors, country, verification_url
  - `SupervisionRecord`: student_name, level (MS/PhD), role (main/co_supervisor), graduation_year

**Prompt Template** (from runner.py EXTRACTION_PROMPT):
```
You are a CV data extraction assistant. Extract structured information from the CV text below.
Return a JSON object that EXACTLY matches this schema. Use these EXACT field names.

SCHEMA: [Full Pydantic schema in JSON format]

RULES:
- Return ONLY valid JSON, no preamble
- For dates: use YYYY-MM or YYYY format
- For lists (authors, authors): return list of strings, not comma-separated
- For years: extract as integer (1990-2030)
- For missing fields: use null, NEVER empty strings
- For degree_level: use only "doctorate", "postgrad", "undergrad", or "school"
- For authorship_role: use only "first", "corresponding", "first_and_corresponding", "co_author"
- For publication type: use only "journal" or "conference"
- For degrees: preserve original text (e.g., "B.Sc. Computer Science", "PhD in Mathematics")

TEXT TO EXTRACT:
[CV TEXT]
```

**Field Validators**: Pydantic validators clean inputs:
- Years: Extracts 4-digit year from any format; ignores "N/A", "None", null
- Dates: Parses "Jan 2020", "2020-01", "January 2020" formats; returns YYYY-MM
- Floats: Removes %, "/4.0", "/5.0" suffix; converts to float
- Enums: Enforces strict string literals for role types

**Output**: Structured `CVExtraction` object with nested data, converted to dict for database storage

**Error Handling:**
- LLM response validation failure: Falls back to empty list for that section
- Malformed JSON: retries extraction up to 3 times
- Pydantic validation failure: logs error, continues with partial data

### 5.3 Module 3.1: Educational Profile Analysis

**Responsibility**: Evaluate candidate educational qualifications, institution prestige, and academic performance.

**Scoring Components** (total: 100 points):

| Component | Max Points | Logic |
|-----------|-----------|-------|
| Degree Level | 25 | Doctorate=25, Postgrad=20, Undergrad=15, School=0 |
| Overall GPA | 30 | Weighted avg: Doctorate×3, Postgrad×2, Undergrad×1; mapped to scale 4-30 |
| Institution Quality | 20 | QS ranking: Tier1 (≤500)=18, Tier2 (501-1000)=12, Tier3 (1001+)=6 |
| Consistency | 15 | Degree progression check: no anomalies (e.g., postgrad before UG) |
| Data Completeness | 10 | Bonus for all fields present (year, cgpa, institution) |

**Institution Quality Scoring** (qs_ranker.py):
- Step 1: **QS Matrix** (fuzzy matching against QS CSV dataset)
  - Normalizes institution names (lowercase, strip spaces)
  - Attempts substring matching first (fastest)
  - Falls back to difflib with cutoff=0.75 (e.g., "MIT" matches "Massachusetts Institute of Technology")
  - Extracts rank from formatted strings ("=401", "1001-1200") → maps to tier
- Step 2: **LLM Fallback** (if QS match fails)
  - Calls LLM with institution name for prestige estimation
  - Falls back to Tier 3 if LLM unavailable

**Output**: EducationScore database record with:
- `score` (0-100)
- `grade` ("EXCELLENT", "GOOD", "AVERAGE", "WEAK")
- `components` dict with breakdown of each sub-score
- `interpretation` text for human review

### 5.4 Module 3.2: Research Performance Analysis

**Responsibility**: Evaluate research output across publications, books, patents, and student supervision.

**Scoring Components** (total: 100 points):

| Component | Max Points | Logic |
|-----------|-----------|-------|
| Journal Publications | 35 | Quality score based on journal quartile, WoS/Scopus indexing, impact factor |
| Conference Publications | 15 | Quality score based on CORE ranking (A*, A, B, C), recency |
| Authorship Analysis | 20 | First author bonus (5 pts/paper), corresponding bonus (3 pts/paper) |
| Books & Patents | 15 | Published books (3 pts each, capped), patents (5 pts each, capped) |
| Student Supervision | 10 | PhD students (2 pts each), MS students (1 pt each) |
| Co-author Collaboration | 5 | Bonus for diverse collaborators (5+ unique co-authors) |

**Publication Metadata Recovery** (research_scores.py):
- **Step 0: Title-based Recovery**
  - For publications missing DOI/ISSN, uses **CrossRef API title search**
  - Recovers: DOI, ISSN, venue, publisher, publication type, year
  - Validates with fuzzy similarity ≥ 0.82 and CrossRef confidence ≥ 85
  - Falls back to OpenAlex if CrossRef score too low

- **Step 1: Journal Quality Scoring**
  - Looks up ISSN in **Scimago Journal Rankings 2025** dataset (CSV with `;` delimiter)
  - Extracts quartile: Q1 (20 pts), Q2 (15 pts), Q3 (10 pts), Q4 (5 pts)
  - Checks **WoS and Scopus indexing** status via cached dataset
  - Scales score by recency: penalty for papers >10 years old

- **Step 2: Conference Quality Scoring**
  - Looks up conference name in **CORE portal ranking CSV**
  - Maps: A* (20 pts), A (15 pts), B (10 pts), C (5 pts), unranked (2 pts)
  - Checks conference series maturity (established ≥5 years)
  - Verifies proceedings indexed by IEEE, ACM, or Springer

- **Step 3: Authorship Analysis**
  - **First author**: +5 points per paper (strong research leadership indicator)
  - **Corresponding author**: +3 points (responsibility and communication)
  - **Co-author**: +1 point (collaboration, but weaker signal)
  - Extracted from "authorship_role" field in extracted data

**Output**: ResearchScore record with:
- `score` (0-100)
- `grade` ("EXCELLENT", "GOOD", "AVERAGE", "WEAK")
- `publications_breakdown` dict with journal/conference/book/patent subcounts
- `interpretation` with specific findings

**API Calls** (async, concurrent):
- CrossRef: title search for DOI/metadata recovery
- OpenAlex: publication metadata and citation counts
- Local CSV lookups: Scimago, CORE, WoS datasets (cached)

### 5.5 Module 3.3: Professional Experience & Career Progression

**Responsibility**: Evaluate job history, career advancement, and domain expertise consistency.

**Scoring Components** (Module 3.8, total: 60 points):

| Component | Max Points | Logic |
|-----------|-----------|-------|
| Timeline Consistency | 20 | No overlaps, no long gaps; gap justification matching |
| Career Progression | 25 | Role seniority advancement (intern→senior→manager), tenure growth |
| Data Quality | 15 | Bonus for complete job descriptions and duration |

**Timeline Analysis**:
- **Gap Detection** (8 pts): Calculates months between end_date of job N and start_date of job N+1
  - No gaps or small gaps (<6 months): full 8 pts
  - Moderate gaps (6-18 months): 4 pts (possible graduate school)
  - Large gaps (>18 months): 0 pts unless gap is justified
- **Overlap Analysis** (6 pts): Checks for job overlaps (impossible timeline)
- **Gap Justification** (6 pts): Scans description for keywords indicating valid gaps:
  - Educational: "phd", "ms", "msc", "master", "study"
  - Sabbatical/Break: "sabbatical", "family", "health"
  - Entrepreneurial: "startup", "freelance", "consulting"
  - Full pts if gap justified; 0 if not explained

**Career Progression**:
- **Seniority Mapping** (10 pts): Extracts key words from role title:
  - Intern/Trainee/Student → Level 1
  - Junior/Entry/Graduate → Level 2
  - Engineer/Developer/Analyst/Officer → Level 3
  - Senior/Lead/Principal/Associate Prof → Level 4
  - Manager/Director → Level 5
  - CEO/CTO/Professor/VP → Level 6
  - Score = (final_level - initial_level) × 2.5 (capped at 10)
- **Tenure Consistency** (8 pts): Average job duration and continuity
- **Domain Continuity** (7 pts): Checks if all jobs are in similar domain (e.g., IT, academics, engineering)

### 5.6 Module 3.4: Skill Alignment Analysis

**Responsibility**: Evaluate skill-to-experience and skill-to-publication alignment (total: 40 points).

**Scoring Components** (Module 3.9):

| Component | Max Points | Logic |
|-----------|-----------|-------|
| Skill-to-Experience Match | 18 | NLP-based keyword overlap between skills and job descriptions |
| Skill-to-Publication Match | 12 | Overlap between skills and publication titles/abstracts |
| Skill Consistency | 10 | Low variance in skill requirements across roles |

**Skill Alignment Methodology**:
- **Extracted vs. Inferred Skills**: Distinguish between skills explicitly listed and skills inferred from CV text
- **Evidence Classification**: For each skill, gather evidence strength:
  - **Strong**: Skill appears in multiple publications AND jobs
  - **Partial**: Skill appears in job description OR publication, but not both
  - **Weak**: Skill mentioned once in CV
  - **Unsupported**: Skill declared but no evidence in experience/publications

**Skill-to-Experience** (NLP):
- For each skill, tokenize and match against job descriptions
- Count keyword overlaps (e.g., skill="Machine Learning", job_desc contains "ML" or "neural networks")
- Calculate percentage match; weight by recency of job

**Skill-to-Publication**:
- For each skill, search publication titles and abstracts for matching keywords
- Higher score if skill is core topic of papers (vs. minor mention)

**Special Case**: If ALL skills are inferred (no explicit skills list), Module 3.9 is skipped, and Module 3.8 score is rescaled to 0-100 (from 0-60).

### 5.7 Module 3.5: Topic Variability & Co-author Collaboration

**Responsibility**: Analyze research breadth, topic diversity, and collaboration patterns (informational, not directly scored).

**Topic Variability Analysis** (tvs_ccs_score.py):
- **Input**: List of publication titles and abstracts
- **LLM Clustering**: Calls LLM to group publications into semantic themes (1-5 themes)
- **Output**: TopicVariabilityResult with:
  - `themes`: List of research themes with paper counts and percentages
  - `dominant_theme`: Most common research area
  - `diversity_score`: 0-10 scale (1=highly specialized, 10=very broad)
  - `focus_type`: One of "deep_specialist" | "broad_specialist" | "generalist" | "interdisciplinary"
  - `topic_trend`: "stable" | "shifting" | "expanding" | "insufficient_data"
  - `overall_interpretation`: 2-3 sentence summary

**Co-author Analysis** (tvs_ccs_score.py):
- **Input**: Author lists from publications
- **Collaboration Metrics**:
  - Total unique co-authors (network size)
  - Recurring collaborators (top 5, frequency count)
  - Inter-institutional collaborations (distinct institutions represented)
  - Multi-country collaborations
- **Output**: CoauthorAnalysisScore with:
  - `total_unique_coauthors`: Count
  - `collaboration_breadth`: Ratio of unique coauthors to papers
  - `recurring_collaborators`: List of top collaborators
  - `network_size_category`: "isolated" | "small" | "medium" | "large"
  - `diversity_score`: 0-10 scale
  - `interpretation`: Summary text

---

## 6. Web Application Features

### 6.1 Frontend Pages & Components

#### **Upload Page** (`UploadPage.jsx`)
- **Drag-and-drop PDF upload**: Users can drag PDFs or click to browse
- **File validation**: Checks file type (PDF only), size limit (200MB typical)
- **Batch upload indicator**: Shows how many CVs will be processed
- **Processing progress**: Real-time status bar showing CV count (e.g., "Processing CV 2 of 5")
- **Candidate name display**: Shows extracted name of current CV being processed
- **Error alerts**: Toast notifications for upload failures
- **Auto-redirect**: On completion, redirects to `/candidates`

#### **Candidates Page** (`CandidatesPage.jsx`)
- **Tabular view**: List of all processed candidates with columns:
  - Candidate name
  - Email
  - Overall score (0-100 with color coding)
  - Overall grade (EXCELLENT, GOOD, AVERAGE, WEAK)
  - Processing date
  - Action links (View Details, Delete)
- **Filtering & sorting**: By name, email, score, date
- **Bulk actions**: Delete multiple candidates
- **Responsive grid**: Adapts to mobile/tablet/desktop screens

#### **Candidate Detail Page** (`CandidateDetailPage.jsx`)
- **Personal information**: Name, email, phone (extracted)
- **Education section**:
  - Table of all education records with degree, institution, GPA, graduation year
  - Education score card with breakdown and grade
  - Interpretation and recommendations
- **Experience section**:
  - Timeline visualization of jobs
  - Role titles, companies, employment type, date ranges
  - Professional experience score with career progression analysis
- **Skills section**:
  - Skill list with inferred status badge
  - Skill alignment score with evidence strength (strong/partial/weak/unsupported)
- **Publications section**:
  - Grouped by type (journals vs. conferences)
  - Title, venue, year, authors, authorship role, indexing status
  - Quartile or CORE ranking indicators
  - Research score with quality breakdown
- **Supervision & Books**: List of supervised students, books, patents
- **Overall Score Card**:
  - Weighted average of all module scores
  - Overall grade
  - Module weights visualization (pie chart via Recharts)
  - Final recommendation and interpretation
- **Missing Information**:
  - Highlighted missing fields (e.g., "GPA not found in education")
  - Draft email for candidate follow-up
  - One-click email draft copy

#### **Rankings Page** (`RankingsPage.jsx`)
- **Candidate ranking table**: Sortable by overall score and module-specific scores
- **Configurable weights**: Sliders to adjust module weights (education, research, etc.)
- **Real-time reranking**: Updates ranking as weights change
- **Export**: Download rankings as CSV
- **Detailed score breakdown**: Hover or click to see score composition

### 6.2 Dashboard Visualizations

Using **Recharts** library:

1. **Module Score Breakdown** (Pie Chart)
   - Visual representation of weighted contributions: 25% education, 35% research, 20% experience, 10% topic variability, 10% co-author

2. **Score Trend Over Modules** (Bar Chart)
   - Side-by-side comparison of raw scores across six modules
   - Color-coded by grade (green=EXCELLENT, yellow=GOOD, orange=AVERAGE, red=WEAK)

3. **Education Performance** (Composite Card)
   - Degree level, GPA, institution tier displayed with progress bars
   - Color-coded by percentile

4. **Publication Count by Type** (Donut Chart)
   - Journal vs. conference publication distribution

5. **Timeline Visualization** (Custom HTML)
   - Career timeline showing job progression chronologically
   - Color-coded by seniority level

6. **Live Processing Progress** (Linear Progress Bar)
   - Shows processing status during batch upload (CV 2 of 5)
   - Animated bar with percentage completion

### 6.3 User Interface Components

**Reusable React Components**:
- `ScoreCard`: Displays module score with grade badge and interpretation
- `ScoreBar`: Progress bar for individual score metrics
- `GradeBadge`: Color-coded badge for grade (EXCELLENT, GOOD, AVERAGE, WEAK)
- `PublicationCard`: Compact publication display with metadata
- `SkillsTab`: Tab view for skills with evidence classification
- `StatChip`: Small statistics display (e.g., "5 publications", "3.8 GPA")
- `SkeletonLoader`: Loading state while data fetches
- `BadgeFlag`: Country/flag badge for international indicators
- `ThemeToggle`: Dark/light mode switcher
- `AppSidebar`: Navigation sidebar with routes to Upload, Candidates, Rankings

**Styling**:
- **Tailwind CSS**: Utility-first responsive design
- **CSS Variables**: Theme system with `--bg-base`, `--bg-border`, `--text-primary`, etc.
- **Dark Mode**: Uses CSS custom properties, toggled via context
- **Responsive Breakpoints**: Mobile (sm), tablet (md), desktop (lg)

### 6.4 API Endpoints

**FastAPI Backend Endpoints** (main.py):

| Method | Endpoint | Purpose | Response |
|--------|----------|---------|----------|
| POST | `/upload` | Upload PDF file(s) for processing | `{"upload_id": "...", "filename": "...", "message": "..."}` |
| GET | `/live-updates` | Poll processing status by upload_id | `{"status": "processing", "current_cv": 2, "total_cvs": 5, "queue_depth": 1, ...}` |
| GET | `/candidates` | List all processed candidates | `[{"id": 1, "name": "...", "email": "...", "overall_score": 85}, ...]` |
| GET | `/candidates/{id}` | Get detailed profile of one candidate | Full CandidateDetailSchema (education, experience, scores, etc.) |
| DELETE | `/candidates/{id}` | Delete candidate and associated data | `{"message": "Candidate deleted"}` |
| GET | `/recommendations/{id}` | Get missing info and email draft | `{"missing_info": [...], "email_body": "..."}` |
| POST | `/email` | Send recommendation email to candidate | `{"success": true, "message": "Email sent"}` |

**Response Schema Examples**:

```json
// GET /candidates/1 response structure:
{
  "id": 1,
  "candidate_id": "sha256hash_12chars",
  "name": "Dr. John Doe",
  "email": "john@example.com",
  "phone": "+1-234-567-8900",
  "education": [
    {
      "degree": "PhD in Computer Science",
      "field": "Computer Science",
      "institution": "MIT",
      "cgpa": 3.95,
      "start_year": 2015,
      "end_year": 2019
    }
  ],
  "publications": [
    {
      "type": "journal",
      "title": "Efficient Neural Networks for Edge Computing",
      "venue": "IEEE Transactions on Computers",
      "year": 2022,
      "authors": ["John Doe", "Jane Smith"],
      "authorship_role": "first",
      "quartile": "Q1",
      "wos_indexed": true
    }
  ],
  "scores": {
    "education_score": {
      "score": 92,
      "grade": "EXCELLENT",
      "components": {...}
    },
    "research_score": {
      "score": 88,
      "grade": "EXCELLENT"
    },
    "experience_score": {
      "score": 75,
      "grade": "GOOD"
    },
    "overall_score": 86,
    "overall_grade": "EXCELLENT"
  }
}
```

---

## 7. Database & Data Schema

### 7.1 Database Choice & Configuration

**Production**: PostgreSQL 15 (Docker container)
**Development**: SQLite (file-based, for rapid iteration)
**Connection Pooling**: SQLAlchemy with async support
**ORM**: SQLAlchemy with Pydantic v2 integration

**Docker Compose Services**:
```yaml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: talash
      POSTGRES_PASSWORD: talash123
      POSTGRES_DB: talash_db
    ports: ["5432:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]
  
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    command: redis-server --appendonly yes
```

### 7.2 Core Tables & Relationships

#### **Table: candidates**
| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | INTEGER | PK, auto_increment | Primary key |
| candidate_id | VARCHAR | UNIQUE, NOT NULL | SHA-256 fingerprint of CV (12 chars) |
| name | VARCHAR | NULL | Full name extracted from CV |
| email | VARCHAR | NULL | Email address |
| phone | VARCHAR | NULL | Phone number |

**Relationships**:
- `1:N` with `education` (one candidate has many degrees)
- `1:N` with `experience` (one candidate has many jobs)
- `1:N` with `skills` (one candidate has many skills)
- `1:N` with `publications` (one candidate has many papers)
- `1:N` with `books` (one candidate has many books)
- `1:N` with `patents` (one candidate has many patents)
- `1:N` with `supervised_students` (one candidate supervises many students)
- `1:1` with `cv_summary` (one candidate has one summary)
- `1:N` with score tables (education_scores, research_scores, etc.)

#### **Table: education**
| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER | PK |
| candidate_id | INTEGER | FK → candidates.id |
| degree | VARCHAR | e.g., "B.Sc. Computer Science" |
| degree_level | VARCHAR | "doctorate", "postgrad", "undergrad", "school" |
| field | VARCHAR | e.g., "Computer Science" |
| institution | VARCHAR | e.g., "MIT" |
| board | VARCHAR | For school-level (SSC, HSSC), e.g., "CBSE" |
| start_year | INTEGER | Graduation year (or start year) |
| end_year | INTEGER | Graduation year |
| cgpa | FLOAT | e.g., 3.95 |
| cgpa_scale | FLOAT | e.g., 4.0 |
| percentage | FLOAT | e.g., 85.5 |
| normalized_percentage | FLOAT | Normalized to 0-100 scale |

#### **Table: experience**
| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER | PK |
| candidate_id | INTEGER | FK → candidates.id |
| company | VARCHAR | e.g., "Google" |
| role | VARCHAR | e.g., "Senior Software Engineer" |
| employment_type | VARCHAR | "Full-time", "Part-time", "Contract", "Freelance" |
| start_date | VARCHAR | ISO format "YYYY-MM" |
| end_date | VARCHAR | ISO format "YYYY-MM" or "current"/"present" |
| description | TEXT | Job responsibilities and achievements |

#### **Table: skills**
| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER | PK |
| candidate_id | INTEGER | FK → candidates.id |
| skill_name | VARCHAR | e.g., "Python", "Machine Learning" |
| inferred | BOOLEAN | TRUE if extracted from CV text, FALSE if explicitly listed |

#### **Table: publications**
| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER | PK |
| candidate_id | INTEGER | FK → candidates.id |
| pub_type | ENUM | "journal" or "conference" |
| title | TEXT | Publication title |
| venue | VARCHAR | Journal/conference name |
| issn | VARCHAR | Journal ISSN (for journal articles) |
| year | INTEGER | Publication year |
| authors | TEXT | Comma-separated author list |
| authorship_role | ENUM | "first", "corresponding", "first_and_corresponding", "co_author" |
| wos_indexed | BOOLEAN | Is paper indexed in Web of Science? |
| scopus_indexed | BOOLEAN | Is paper indexed in Scopus? |
| quartile | VARCHAR | "Q1", "Q2", "Q3", "Q4" (for journals) |
| impact_factor | FLOAT | Journal IF (if available) |
| journal_name | VARCHAR | Normalized journal name (from metadata recovery) |
| conference_name | VARCHAR | Normalized conference name (from CORE lookup) |
| core_rank | VARCHAR | "A*", "A", "B", "C" (for conferences) |

#### **Table: books**
| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER | PK |
| candidate_id | INTEGER | FK → candidates.id |
| title | VARCHAR | Book title |
| authors | TEXT | Author list |
| isbn | VARCHAR | ISBN |
| publisher | VARCHAR | Publisher name |
| year | INTEGER | Publication year |
| url | VARCHAR | Link to book (Google Books, publisher) |
| authorship_role | VARCHAR | "sole", "lead", "co_author", "contributing" |

#### **Table: patents**
| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER | PK |
| candidate_id | INTEGER | FK → candidates.id |
| patent_number | VARCHAR | e.g., "US10234567B2" |
| title | VARCHAR | Patent title |
| year | INTEGER | Filing or grant year |
| inventors | TEXT | Inventor list |
| country | VARCHAR | Patent country (US, EP, IN, etc.) |
| verification_url | VARCHAR | Link to patent office record |

#### **Table: supervised_students**
| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER | PK |
| candidate_id | INTEGER | FK → candidates.id |
| student_name | VARCHAR | Name of supervised student |
| level | ENUM | "MS" or "PhD" |
| role | ENUM | "main" or "co_supervisor" |
| graduation_year | INTEGER | Student's graduation year |

#### **Table: cv_summary**
| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER | PK |
| candidate_id | INTEGER | FK → candidates.id (UNIQUE, one-to-one) |
| executive_summary | TEXT | AI-generated 3-5 sentence summary |
| key_strengths | TEXT | JSON array of top 3-5 strengths |
| key_weaknesses | TEXT | JSON array of limitations/gaps |
| missing_fields | TEXT | JSON array of missing information |
| recommendations | TEXT | JSON array of hiring recommendations |
| generated_email_draft | TEXT | HTML email body for follow-up |
| timestamp | DATETIME | When summary was generated |

### 7.3 Scoring Tables

#### **Table: education_scores**
| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER | PK |
| candidate_id | INTEGER | FK → candidates.id |
| score | FLOAT | Final score (0-100) |
| grade | VARCHAR | "EXCELLENT", "GOOD", "AVERAGE", "WEAK" |
| components | JSON | Breakdown: {degree_level, gpa, institution, consistency, completeness, ...} |
| interpretation | TEXT | Human-readable explanation of score |
| timestamp | DATETIME | When calculated |

#### **Table: research_scores**
| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER | PK |
| candidate_id | INTEGER | FK → candidates.id |
| score | FLOAT | Final score (0-100) |
| grade | VARCHAR | Grade label |
| journal_count | INTEGER | Number of journal publications |
| conference_count | INTEGER | Number of conference publications |
| first_author_count | INTEGER | Number of papers where candidate is first author |
| book_count | INTEGER | Number of published books |
| patent_count | INTEGER | Number of patents |
| phd_students | INTEGER | Number of PhD students supervised |
| ms_students | INTEGER | Number of MS students supervised |
| components | JSON | Detailed breakdown of scoring |
| interpretation | TEXT | Summary of research profile |
| timestamp | DATETIME | When calculated |

#### **Table: professional_experience_scores**
| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER | PK |
| candidate_id | INTEGER | FK → candidates.id |
| score | FLOAT | Final score (0-100) |
| grade | VARCHAR | Grade label |
| timeline_consistency_score | FLOAT | Gap/overlap analysis |
| career_progression_score | FLOAT | Seniority advancement |
| components | JSON | Detailed breakdown |
| interpretation | TEXT | Career trajectory summary |
| timestamp | DATETIME | When calculated |

#### **Table: skill_alignment_scores**
| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER | PK |
| candidate_id | INTEGER | FK → candidates.id |
| score | FLOAT | Final score (0-100) |
| grade | VARCHAR | Grade label |
| skill_experience_match | FLOAT | Overlap with job descriptions |
| skill_publication_match | FLOAT | Overlap with research papers |
| skill_consistency | FLOAT | Variance across roles |
| components | JSON | Skill evidence mapping |
| interpretation | TEXT | Skill alignment summary |
| timestamp | DATETIME | When calculated |

#### **Table: topic_variability_scores**
| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER | PK |
| candidate_id | INTEGER | FK → candidates.id |
| diversity_score | FLOAT | 0-10 scale |
| focus_type | VARCHAR | "deep_specialist", "broad_specialist", "generalist", "interdisciplinary" |
| themes | JSON | Array of identified research themes |
| dominant_theme | VARCHAR | Most common research area |
| topic_trend | VARCHAR | "stable", "shifting", "expanding" |
| interpretation | TEXT | Research breadth summary |
| timestamp | DATETIME | When calculated |

#### **Table: coauthor_analysis_scores**
| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER | PK |
| candidate_id | INTEGER | FK → candidates.id |
| total_unique_coauthors | INTEGER | Number of distinct collaborators |
| collaboration_breadth | FLOAT | Ratio of unique to total collaborations |
| network_size_category | VARCHAR | "isolated", "small", "medium", "large" |
| recurring_collaborators | JSON | Top 5 frequent collaborators |
| diversity_score | FLOAT | 0-10 scale |
| interpretation | TEXT | Collaboration summary |
| timestamp | DATETIME | When calculated |

### 7.4 Database Relationships Diagram

```
candidates (1) ───→ (N) education
         ├──→ (N) experience
         ├──→ (N) skills
         ├──→ (N) publications
         ├──→ (N) books
         ├──→ (N) patents
         ├──→ (N) supervised_students
         ├──→ (1) cv_summary
         ├──→ (1) education_scores
         ├──→ (1) research_scores
         ├──→ (1) professional_experience_scores
         ├──→ (1) skill_alignment_scores
         ├──→ (1) topic_variability_scores
         └──→ (1) coauthor_analysis_scores
```

### 7.5 Initialization & Migration

**Database Setup** (db_connect.py):
```python
def init_db():
    # Create all tables from Base metadata
    Base.metadata.create_all(engine)
    print("Database initialized")

# Called at app startup in main.py
init_db()
```

---

## 8. LLM Prompting Strategy

### 8.1 LLM Provider Selection & Fallback

**Primary Hierarchy**:
1. **Groq (llama-3.3-70b-versatile)**: Free tier, very fast (2-5s/request), supports structured output
2. **Google Gemini (gemini-2.0-flash)**: Fallback, free tier, reliable
3. **OpenRouter (/auto)**: Last resort, auto-selects best available model

**Multi-Key Rotation**:
```python
# Support 5 API keys per provider for rate limit spreading
groq_keys = [LITELLM_GROQ_API_KEY1, ..., LITELLM_GROQ_API_KEY5]
gemini_keys = [LITELLM_GEMINI_API_KEY1, ..., LITELLM_GEMINI_API_KEY5]

# Round-robin key rotation
groq_index = 0
groq_index = (groq_index + 1) % len(groq_keys)  # Next request uses next key
```

### 8.2 Task Decomposition: LLM vs. Rule-Based

| Task | Approach | Reasoning |
|------|----------|-----------|
| **CV Text Extraction** | LLM (structured) | Handles format variability, contextual understanding |
| **Personal Info Extraction** | LLM | Name, email, phone in unstructured text |
| **Education Extraction** | LLM | Degree parsing, institution recognition |
| **Experience Extraction** | LLM | Complex job descriptions, date parsing |
| **Publication Extraction** | LLM | Title, venue, authors in variable formats |
| **GPA Normalization** | Rule-based | Conversion to 0-100 scale (simple math) |
| **Degree Level Classification** | Rule-based | Regex + hardcoded keyword mapping |
| **Year Parsing** | Rule-based (Pydantic validator) | Regex extraction of 4-digit years |
| **Date Parsing** | Rule-based (Pydantic validator) | Month/year parsing with multiple formats |
| **QS Ranking Lookup** | Rule-based (fuzzy matching + CSV) | Dataset lookup, no LLM needed |
| **Journal Quartile Lookup** | Rule-based (CSV ISSN lookup) | Scimago dataset, deterministic |
| **CORE Conference Lookup** | Rule-based (CSV name matching) | CORE dataset, no LLM needed |
| **Timeline Gap Detection** | Rule-based (date arithmetic) | Straightforward calculation |
| **Topic Clustering** | LLM (unsupervised) | Semantic understanding of publication themes |
| **Missing Info Detection** | Rule-based (field presence check) | Check if field is NULL or empty |
| **Email Draft Generation** | LLM (template + variables) | Personalized email composition |
| **Summary Generation** | LLM (prompt + data) | Narrative text creation |

**Rationale**:
- **LLM for unstructured → structured**: CVs have extreme format variability; LLM provides semantic understanding
- **Rule-based for deterministic tasks**: Mapping, validation, lookup tasks are faster and more reliable with rules
- **Hybrid for nuanced tasks**: Topic clustering combines LLM (semantic) with rule-based filtering

### 8.3 Prompt Templates & Examples

#### **Prompt 1: CV Data Extraction** (EXTRACTION_PROMPT in runner.py)

```
You are a CV data extraction assistant. Extract structured information from the CV text below.
Return a JSON object that EXACTLY matches this schema. Use these EXACT field names.

SCHEMA:
{
  "personal_info": {
    "name": string or null,
    "email": string or null,
    "phone": string or null
  },
  "education": [
    {
      "degree": string or null,
      "degree_level": string or null,
      "field": string or null,
      "institution": string or null,
      "start_year": integer or null,
      "end_year": integer or null,
      "cgpa": float or null,
      "cgpa_scale": float or null,
      "percentage": float or null,
      "board": string or null
    }
  ],
  "experience": [
    {
      "company": string or null,
      "role": string or null,
      "employment_type": string or null,
      "start_date": string or null,
      "end_date": string or null,
      "description": string or null
    }
  ],
  "skills": [string],
  "publications": [
    {
      "type": "journal" or "conference",
      "title": string or null,
      "venue": string or null,
      "issn": string or null,
      "year": integer or null,
      "authors": [string],
      "authorship_role": "first" or "corresponding" or "first_and_corresponding" or "co_author",
      "wos_indexed": boolean or null,
      "scopus_indexed": boolean or null,
      "quartile": "Q1" or "Q2" or "Q3" or "Q4" or null,
      "impact_factor": float or null
    }
  ],
  "books": [
    {
      "title": string or null,
      "authors": [string],
      "isbn": string or null,
      "publisher": string or null,
      "year": integer or null,
      "url": string or null,
      "authorship_role": string or null
    }
  ],
  "patents": [
    {
      "patent_number": string or null,
      "title": string or null,
      "year": integer or null,
      "inventors": [string],
      "country": string or null,
      "verification_url": string or null
    }
  ],
  "supervised_students": [
    {
      "student_name": string or null,
      "level": "MS" or "PhD" or null,
      "role": "main" or "co_supervisor" or null,
      "graduation_year": integer or null
    }
  ]
}

RULES:
- Return ONLY valid JSON, no preamble or prose
- For dates: use YYYY-MM or YYYY format (e.g., "2020-01" or "2020")
- For years: extract as 4-digit integer (1990-2030 range)
- For lists (authors, inventors, skills): return as array of strings, not comma-separated
- For missing fields: use null, NEVER empty strings ""
- For degree_level: use only "doctorate", "postgrad", "undergrad", or "school"
- For authorship_role: use only "first", "corresponding", "first_and_corresponding", or "co_author"
- For publication type: use only "journal" or "conference"
- For CGPA: if scale given (e.g., "3.95/4.0"), extract number before slash
- For percentage: remove % symbol (e.g., "85.5%" → 85.5)
- For phone: include country code if available (e.g., "+1-234-567-8900")
- If multiple degrees, list each separately in education array
- If current job (end date unknown), set end_date to null or "current"

TEXT TO EXTRACT:
[CV TEXT WILL BE INSERTED HERE]

RESPOND WITH ONLY THE JSON OBJECT:
```

**Pydantic Schema Enforcement**:
```python
structured_llm = llm.with_structured_output(CVExtraction)
response = structured_llm.invoke([
    SystemMessage(content="You are a CV data extraction expert..."),
    HumanMessage(content=f"Extract data from this CV:\n{cv_text}")
])
# Response is validated CVExtraction object with all fields properly typed
```

#### **Prompt 2: Topic Variability Analysis** (tvs_ccs_score.py)

```
Analyze the following research publications and cluster them into semantic research themes.
The candidate has published on the following topics:

[PUBLICATION TITLES AND ABSTRACTS]

Task:
1. Identify 1-5 distinct research themes that organize these publications
2. For each theme, provide:
   - A 3-5 word theme name (e.g., "Computer Vision Applications", "Biomedical Signal Processing")
   - A one-sentence description of what papers in this theme cover
   - Count of papers assigned to this theme
   - Percentage of total publications (0-100)
   - List of paper IDs (as provided)

3. Identify the dominant (most common) research theme

4. Compute a diversity score from 0.0-10.0:
   - 0-2: Highly specialized (1-2 themes, >80% in dominant theme)
   - 3-4: Deep specialist (2-3 themes, 60-80% in dominant)
   - 5-6: Broad specialist (3-4 themes, 40-60% in dominant)
   - 7-8: Generalist (4-5 themes, 20-40% in dominant)
   - 9-10: Interdisciplinary (5+ themes, <20% in dominant)

5. Determine research trend across years:
   - "stable" if theme distribution has not changed significantly
   - "shifting" if research has moved toward new themes in recent years
   - "expanding" if new themes and older ones coexist equally
   - "insufficient_data" if <2 years of publications

6. Provide a 2-3 sentence overall interpretation

RETURN JSON:
{
  "themes": [
    {
      "theme_name": "...",
      "description": "...",
      "paper_count": N,
      "percentage": X.X,
      "paper_ids": [1, 2, 3]
    }
  ],
  "dominant_theme": "...",
  "diversity_score": X.X,
  "focus_type": "deep_specialist|broad_specialist|generalist|interdisciplinary",
  "topic_trend": {"trend": "...", "explanation": "..."},
  "overall_interpretation": "..."
}
```

#### **Prompt 3: Email Draft Generation** (summarizers.py)

```
Generate a professional, friendly email to request missing information from a candidate.

Candidate Name: {name}
Current Overall Score: {score}/100 ({grade})

Missing Information:
- {field1}: {description}
- {field2}: {description}
- ...

Instructions:
1. Write in professional but warm tone
2. Explain why the information matters (e.g., "institution details help us assess your educational background")
3. Ask specific questions for each missing field
4. Provide a deadline (e.g., "by [date]")
5. Include contact information for questions
6. Keep to 3-4 paragraphs max
7. Return as HTML (for email client rendering)

OUTPUT: HTML email body
```

### 8.4 Output Parsing & Validation

**Structured Output Handling** (LangChain):
```python
# LLM outputs Pydantic-validated JSON
structured_llm = llm.with_structured_output(CVExtraction)
result = structured_llm.invoke(messages)
# result is CVExtraction instance (not string)
# Type-safe, no JSON parsing errors

# Convert to dict for storage
result_dict = result.model_dump()
```

**Fallback for Unstructured Outputs**:
```python
# Topic variability returns JSON string
response_text = llm_response.content

# Extract JSON from markdown or prose
cleaned = re.sub(r"^```json\s*|^```\s*|```\s*$", "", response_text, flags=re.MULTILINE).strip()

if not cleaned.startswith("{"):
    start = response_text.find("{")
    end = response_text.rfind("}")
    if start != -1 and end != -1:
        cleaned = response_text[start:end+1]

result = TopicVariabilityResult.model_validate_json(cleaned)
```

**Error Handling**:
- Pydantic validation error → Log error, use default/empty values
- JSON parsing error → Retry up to 2 times with refined prompt
- LLM timeout → Use fallback provider

---

## 9. Challenges Faced and Solutions

### 9.1 Challenge 1: Inconsistent CV Formats and Missing Data

**Problem**:
- CVs are highly unstructured: dates appear as "Jan 2020", "2020-01", "January 2020", "2020"
- Education sections vary: some list GPA, others list percentage; some list institution tier in brackets
- Missing fields are common: many candidates don't list phone numbers or precise GPAs
- LLM extraction can hallucinate data or miss sections entirely

**Impact**:
- Database inconsistency, scoring biases, missed candidate signals

**Solution Implemented**:
1. **Pydantic Field Validators**: Built strict validators for each field type
   ```python
   @field_validator("start_year", mode="before")
   @classmethod
   def parse_year(cls, v):
       if v is None or str(v).strip().lower() in {"n/a","na","none","null",""}:
           return None
       match = re.search(r"\b(19|20)\d{2}\b", str(v))
       return int(match.group()) if match else None
   ```
2. **Null-Safe Defaults**: All list fields default to `[]` (never None)
3. **Date Parsing Pipeline**: Tries 5+ date formats before returning None
4. **Field Presence Checks**: Scoring penalties for missing data, not errors

### 9.2 Challenge 2: LLM Hallucination in Publication Details

**Problem**:
- LLM sometimes generates plausible-sounding but fake journal names, authors, or conference details
- Hallucinated publications inflate research scores unfairly
- CrossRef API calls are expensive (charged per request); can't verify every publication

**Impact**:
- Candidates with fabricated research appear stronger than they are

**Solution Implemented**:
1. **Publication Metadata Recovery (3-Tier)**:
   - Tier 1: CrossRef API lookup by title → returns verified DOI, ISSN, venue, year
   - Tier 2: OpenAlex API fallback (free, more lenient but less precise)
   - Tier 3: Accept LLM extraction only if no API match found
2. **Fuzzy Similarity Thresholds**:
   - CrossRef result must have API confidence ≥ 85% AND fuzzy title match ≥ 0.82
   - Reject partial matches
3. **ISSN Validation**:
   - Cross-check ISSN against Scimago dataset before assigning quartile
   - Invalid ISSNs → default to Q4 or unranked
4. **Confidence Scoring**:
   - Flag publications without verified metadata in database
   - Frontend displays verification status badge

### 9.3 Challenge 3: CGPA Normalization Across Different Scales

**Problem**:
- Candidates from different countries/institutions use different GPA scales:
  - US: 4.0 scale
  - Some universities: 5.0 or 10.0 scale
  - European: sometimes percentages (0-100)
  - Percentages are sometimes 0-100, sometimes weighted differently
- LLM extraction captures raw values but doesn't normalize
- Without normalization, comparing candidates is unfair (a 3.5/4.0 ≠ 3.5/5.0)

**Impact**:
- Unfair scoring; education scores are biased toward certain countries/institutions

**Solution Implemented**:
1. **CGPAsScale Extraction**: LLM extracts both `cgpa` and `cgpa_scale` fields
2. **Normalization Formula**:
   ```python
   normalized_percentage = (cgpa / cgpa_scale) × 100
   # If scale is 4.0: 3.95/4.0 × 100 = 98.75%
   # If scale is 5.0: 3.95/5.0 × 100 = 79.0%
   # If already percentage: 85% remains 85%
   ```
3. **Weighted Averaging**: Uses normalized percentage, not raw GPA
   ```python
   weighted_avg = sum(normalized_pct × weight for each education level) / total_weight
   ```
4. **Fallback**: If scale not provided, assume 4.0 (most common in academic CVs)

### 9.4 Challenge 4: Multiple CVs in Single PDF

**Problem**:
- Sometimes candidates submit PDFs with 3-5 CVs (mine, spouse's, colleague's)
- Simple text splitting (by page) doesn't work; CVs span multiple pages
- Need to identify CV boundaries without external metadata
- Fingerprinting must be unique per CV to prevent false deduplication

**Impact**:
- Without boundary detection, combining multiple CVs into one record; scoring becomes meaningless

**Solution Implemented**:
1. **Heuristic Boundary Detection** (detect_cv_boundaries in runner.py):
   ```python
   _CV_KEYWORD_RE = re.compile(r"curriculum\s+vitae|\bresume\b|\bbiodata\b", re.IGNORECASE)
   _EMAIL_RE = re.compile(r"\b[\w.+\-]+@[\w\-]+\.[a-z]{2,}\b")
   _PHONE_RE = re.compile(r"(\+?\d[\d\s\-\(\)]{7,}\d)")
   
   def _looks_like_cv_start(page_text):
       sample = page_text[:600]
       has_cv_keyword = bool(_CV_KEYWORD_RE.search(sample))
       has_email = bool(_EMAIL_RE.search(sample))
       has_phone = bool(_PHONE_RE.search(sample))
       has_name_label = bool(_NAME_LABEL_RE.search(sample))
       
       # Signal: cv_keyword + (email or phone), or name_label + email
       if has_cv_keyword and (has_email or has_phone):
           return True
       if has_name_label and has_email:
           return True
       return False
   ```
2. **Sequential Boundary Detection**:
   - Iterate through extracted pages
   - When `_looks_like_cv_start()` detects a new CV, save current CV and start new one
   - Filter out short fragments (< 200 chars)
3. **Unique Fingerprinting**:
   ```python
   fingerprint = SHA256(cv_text[:1000]).hexdigest()[:12]
   # Different CVs → different first-1000 chars → different fingerprints
   # Same CV (re-upload) → same fingerprint → cache hit
   ```

### 9.5 Challenge 5: Institution Prestige Scoring with Limited Data

**Problem**:
- QS World University Rankings only cover ~1200 universities; most of the world's ~30k institutions are unranked
- Fuzzy matching is error-prone (e.g., "UC Berkeley" vs. "University of California, Berkeley")
- Different naming conventions (abbreviations, local names, transliteration issues)
- LLM fallback can hallucinate tier assignments

**Impact**:
- Candidates from unranked but quality institutions are unfairly penalized
- Over-reliance on LLM leads to inconsistent scoring

**Solution Implemented**:
1. **Multi-Stage Fuzzy Matching** (qs_ranker.py):
   ```python
   # Stage 1: Substring containment (fastest)
   if institution_name[:20] in df['_normalized']:
       return matched_row
   
   # Stage 2: Reverse substring (institution name is substring of input)
   if df['_normalized'].contains(institution_name[:20]):
       return matched_row
   
   # Stage 3: Difflib with cutoff=0.75 (handles variations)
   matches = difflib.get_close_matches(normalized_input, qs_names, n=1, cutoff=0.75)
   ```
2. **Rank Parsing**: Handles formatted ranks ("=401", "1001-1200", "1501+")
   ```python
   def _parse_rank(rank_str):
       # Range: take upper bound
       if '-' in rank_str:
           return int(rank_str.split('-')[-1])
       return int(rank_str.replace('=', '').replace('+', ''))
   ```
3. **Tier Mapping** (conservative):
   - Tier 1 (score 18): Rank ≤ 500
   - Tier 2 (score 12): Rank 501-1000
   - Tier 3 (score 6): Rank 1001+ or unranked
4. **LLM Fallback Only**: When QS match fails; logs fall-back usage for manual review
5. **Data Completeness Bonus**: Candidates with complete education info get bonus 10 pts (encouraging data submission)

### 9.6 Challenge 6: Handling LLM Timeout & API Rate Limits

**Problem**:
- Groq API occasionally times out or hits rate limits (especially with free tier)
- Batch processing 50 CVs can trigger 50+ LLM calls; without fallback, any single failure blocks pipeline
- Different API providers have different limits and latencies
- Multi-key rotation helps but isn't foolproof

**Impact**:
- Processing failures, user-facing "something went wrong" errors, incomplete candidate records

**Solution Implemented**:
1. **Multi-Provider Fallback Chain** (llm_client.py):
   ```python
   def litellm_chat(user_prompt, system_prompt, provider="groq"):
       try:
           # Tier 1: Groq (fastest)
           response = litellm.completion(model="groq/llama-3.3-70b-versatile", ...)
       except Exception as e:
           print(f"Groq failed, falling back to Gemini: {e}")
           # Tier 2: Gemini
           response = litellm.completion(model="gemini/gemini-2.0-flash", ...)
       except Exception as e:
           print(f"Gemini failed, falling back to OpenRouter: {e}")
           # Tier 3: OpenRouter auto
           response = litellm.completion(model="openrouter/auto", ...)
   ```
2. **Multi-Key Rotation**:
   - 5 Groq API keys, 5 Gemini keys
   - Round-robin rotation spreads load
   - Rate limit on key1 → next request uses key2
3. **Per-CV Error Handling**: Single CV extraction failure logs error but continues with next CV
4. **Timeout Configuration**: Set explicit timeouts (e.g., 30s per request)
5. **Async Queue**: Background worker processes one CV at a time; failed CV is removed from queue, not retried

### 9.7 Challenge 7: Scoring Parity Across Different CV Formats

**Problem**:
- Academic CVs vs. industry resumes have very different structures
- Some candidates list extensive publications; others focus on industry roles
- Scoring weights (25% education, 35% research) are tailored to faculty hiring
- Research score would unfairly bias industry professionals with few publications
- Need fair scoring for diverse backgrounds

**Impact**:
- Bias in scoring; industry professionals with strong teaching skills penalized

**Solution Implemented**:
1. **Flexible Module Weighting**:
   - Default weights: education 25%, research 35%, experience 20%, skills/variability 10%, collaboration 10%
   - Frontend allows users to adjust weights in real-time (Sliders on Rankings Page)
   - Candidates are re-ranked based on custom weights
2. **Module-Specific Grading** (not just raw score):
   - Each module produces both raw score AND grade (EXCELLENT, GOOD, AVERAGE, WEAK)
   - Grade reflects percentile within that module, not absolute points
3. **Data Completeness Bonus**:
   - Candidates with comprehensive CVs get overall boost
   - Encourages detailed submission regardless of field
4. **Interpretation Transparency**:
   - Every score includes human-readable justification
   - Evaluators understand why a score was given
   - Can override or apply context in decision-making

---

## 10. Results and Sample Outputs

### 10.1 Sample Candidate Processing

**Input**: A PDF CV from Dr. Sarah Chen, a computer science researcher with 12 years of academic experience.

**Extraction Result** (CVExtraction):
```json
{
  "personal_info": {
    "name": "Dr. Sarah Chen",
    "email": "s.chen@university.edu",
    "phone": "+1-555-123-4567"
  },
  "education": [
    {
      "degree": "PhD in Computer Science",
      "degree_level": "doctorate",
      "field": "Computer Science",
      "institution": "Carnegie Mellon University",
      "start_year": 2008,
      "end_year": 2012,
      "cgpa": 3.92,
      "cgpa_scale": 4.0,
      "percentage": null,
      "normalized_percentage": 98.0
    },
    {
      "degree": "Bachelor of Science in Computer Engineering",
      "degree_level": "undergrad",
      "field": "Computer Engineering",
      "institution": "UC Berkeley",
      "start_year": 2004,
      "end_year": 2008,
      "cgpa": 3.85,
      "cgpa_scale": 4.0,
      "percentage": null,
      "normalized_percentage": 96.25
    }
  ],
  "experience": [
    {
      "company": "Tech University",
      "role": "Associate Professor",
      "employment_type": "Full-time",
      "start_date": "2018-08",
      "end_date": null,
      "description": "Lead AI and machine learning research group. Teach undergraduate and graduate courses in algorithms and distributed systems. Supervise PhD and MS students."
    },
    {
      "company": "Google Research",
      "role": "Senior Research Scientist",
      "employment_type": "Full-time",
      "start_date": "2015-06",
      "end_date": "2018-07",
      "description": "Developed neural network architectures for natural language processing. Published 8 papers in top venues. Led team of 3 junior researchers."
    }
  ],
  "skills": ["Python", "Machine Learning", "TensorFlow", "Natural Language Processing", "Research Leadership", "Academic Writing"],
  "publications": [
    {
      "type": "journal",
      "title": "Efficient Transformer Architectures for Real-Time NLP",
      "venue": "IEEE Transactions on Pattern Analysis and Machine Intelligence",
      "issn": "0162-8828",
      "year": 2022,
      "authors": ["Sarah Chen", "David Lee", "Emily Watson"],
      "authorship_role": "first",
      "wos_indexed": true,
      "scopus_indexed": true,
      "quartile": "Q1",
      "impact_factor": 24.5
    },
    {
      "type": "conference",
      "title": "Attention is Not Enough: Combining Recurrence with Self-Attention",
      "venue": "International Conference on Machine Learning",
      "year": 2021,
      "authors": ["Sarah Chen", "Alex Kumar", "Robert Smith"],
      "authorship_role": "first",
      "wos_indexed": true,
      "scopus_indexed": true,
      "core_rank": "A*"
    }
  ],
  "books": [],
  "patents": [],
  "supervised_students": [
    {
      "student_name": "Michael Zhang",
      "level": "PhD",
      "role": "main",
      "graduation_year": 2023
    },
    {
      "student_name": "Lisa Wang",
      "level": "PhD",
      "role": "main",
      "graduation_year": null
    },
    {
      "student_name": "James Patel",
      "level": "MS",
      "role": "main",
      "graduation_year": 2023
    }
  ]
}
```

### 10.2 Sample Scoring Results

**Education Score** (Module 3.1):
```json
{
  "score": 95,
  "grade": "EXCELLENT",
  "components": {
    "degree_level": {
      "score": 25,
      "max": 25,
      "reason": "PhD from Carnegie Mellon University"
    },
    "overall_gpa": {
      "score": 29,
      "max": 30,
      "reason": "Weighted avg: 97.1% (Doctorate 98.0%×3 + Undergrad 96.25%×1 / 4)",
      "weighted_avg": 97.13
    },
    "institution_quality": {
      "score": 20,
      "max": 20,
      "reason": "Tier 1 (QS rank 32 for CMU)",
      "tier": 1,
      "institution": "Carnegie Mellon University"
    },
    "consistency": {
      "score": 15,
      "max": 15,
      "reason": "Consistent progression: UG → PhD, no anomalies"
    },
    "data_completeness": {
      "score": 6,
      "max": 10,
      "reason": "GPA, years, and institutions provided for all degrees"
    }
  },
  "interpretation": "Excellent educational background with PhD from top-tier institution (CMU, rank 32) and outstanding academic performance (98% GPA). Strong foundation for faculty role.",
  "timestamp": "2024-12-01T10:30:00Z"
}
```

**Research Score** (Module 3.2):
```json
{
  "score": 92,
  "grade": "EXCELLENT",
  "journal_count": 8,
  "conference_count": 12,
  "first_author_count": 15,
  "book_count": 0,
  "patent_count": 0,
  "phd_students": 2,
  "ms_students": 3,
  "components": {
    "journal_publications": {
      "score": 32,
      "max": 35,
      "breakdown": "4 Q1 papers (80 pts), 2 Q2 papers (30 pts), 2 Q3 papers (20 pts) = 130 pts raw, capped at 32"
    },
    "conference_publications": {
      "score": 14,
      "max": 15,
      "breakdown": "3 A* papers (60 pts), 5 A papers (75 pts), 4 B papers (40 pts) = 175 raw, capped at 14"
    },
    "authorship_analysis": {
      "score": 19,
      "max": 20,
      "breakdown": "15 first-author papers (75 pts), 5 corresponding-author papers (15 pts) / 20 total"
    },
    "supervision": {
      "score": 10,
      "max": 10,
      "breakdown": "2 PhD students (4 pts) + 3 MS students (3 pts) + 1 postdoc (3 pts) = 10/10"
    },
    "collaboration": {
      "score": 5,
      "max": 5,
      "breakdown": "20+ unique co-authors across publications, excellent collaboration network"
    }
  },
  "interpretation": "Outstanding research profile: 20 publications with 15 as first author, predominantly in top-tier venues (Q1/A* ranked). Strong supervision record (5 mentored students). Excellent collaboration breadth. Research impact well-suited for faculty role.",
  "timestamp": "2024-12-01T10:32:00Z"
}
```

**Professional Experience Score** (Module 3.3):
```json
{
  "score": 88,
  "grade": "EXCELLENT",
  "components": {
    "timeline_consistency": {
      "score": 20,
      "max": 20,
      "gap_detection": 8,
      "overlap_analysis": 6,
      "gap_justification": 6,
      "reasoning": "Clean timeline: Berkeley (2004-2008) → CMU PhD (2008-2012) → Google (2015-2018) → Current position (2018-present). Small gaps justified by PhD completion and job transitions."
    },
    "career_progression": {
      "score": 24,
      "max": 25,
      "seniority_advancement": 10,
      "tenure_consistency": 8,
      "domain_continuity": 6,
      "reasoning": "Clear progression: Research Scientist (Google) → Associate Professor (current). Long tenure in academic + industry. Consistent domain (ML/NLP)."
    },
    "data_quality": {
      "score": 14,
      "max": 15,
      "reasoning": "Complete job descriptions, date ranges, and role titles provided. Minor deduction for current role end date."
    }
  },
  "interpretation": "Strong professional trajectory combining industry research leadership (Google) with academic advancement (Associate Professor). Demonstrates progression from individual contributor to team leader and faculty. Excellent domain continuity.",
  "timestamp": "2024-12-01T10:34:00Z"
}
```

**Skill Alignment Score** (Module 3.4):
```json
{
  "score": 82,
  "grade": "EXCELLENT",
  "components": {
    "skill_experience_match": {
      "score": 16,
      "max": 18,
      "evidence": {
        "Python": "Strong - mentioned in Google role, publications, teaching",
        "Machine Learning": "Strong - 8+ publications, core role at Google",
        "TensorFlow": "Partial - mentioned in publications but not explicitly in job descriptions",
        "Academic Writing": "Strong - 20 publications, book chapters"
      }
    },
    "skill_publication_match": {
      "score": 11,
      "max": 12,
      "evidence": "NLP, ML, Transformers, Attention mechanisms directly reflected in publication titles and venue choices"
    },
    "skill_consistency": {
      "score": 9,
      "max": 10,
      "reasoning": "Consistent core skills (ML, NLP) across all roles. No anomalous skill claims."
    }
  },
  "interpretation": "Skills well-aligned with experience and research output. ML/NLP expertise is demonstrated through publications and roles. Some technical skills (TensorFlow) have partial evidence. Overall strong skill consistency.",
  "timestamp": "2024-12-01T10:36:00Z"
}
```

**Topic Variability Score** (Module 3.5):
```json
{
  "diversity_score": 7.2,
  "focus_type": "broad_specialist",
  "themes": [
    {
      "theme_name": "Efficient Neural Architectures",
      "description": "Research on optimizing neural networks for speed, memory, and edge deployment",
      "paper_count": 7,
      "percentage": 35,
      "paper_ids": [1, 2, 3, 4, 5, 6, 7]
    },
    {
      "theme_name": "Natural Language Understanding",
      "description": "Semantic understanding, question answering, and language representation learning",
      "paper_count": 6,
      "percentage": 30,
      "paper_ids": [8, 9, 10, 11, 12, 13]
    },
    {
      "theme_name": "Transformer Models & Attention",
      "description": "Analysis and improvements to transformer architectures and self-attention mechanisms",
      "paper_count": 5,
      "percentage": 25,
      "paper_ids": [14, 15, 16, 17, 18]
    },
    {
      "theme_name": "Machine Learning for Robotics",
      "description": "Deep reinforcement learning and computer vision for robotic control",
      "paper_count": 2,
      "percentage": 10,
      "paper_ids": [19, 20]
    }
  ],
  "dominant_theme": "Efficient Neural Architectures",
  "topic_trend": {
    "trend": "shifting",
    "explanation": "Earlier publications (2015-2017) focused on general deep learning; recent work (2020-2024) emphasizes efficiency and transformer optimization for edge deployment."
  },
  "overall_interpretation": "Research demonstrates broad expertise across ML/NLP with a specialization in efficient neural architectures. Focus has shifted toward practical deployment optimization in recent years. Shows both depth (dominated by architecture work) and breadth (4 distinct themes).",
  "timestamp": "2024-12-01T10:38:00Z"
}
```

**Co-author Analysis Score** (Module 3.6):
```json
{
  "total_unique_coauthors": 24,
  "collaboration_breadth": 1.2,
  "recurring_collaborators": [
    {"name": "David Lee", "paper_count": 5},
    {"name": "Emily Watson", "paper_count": 4},
    {"name": "Robert Smith", "paper_count": 3},
    {"name": "Alex Kumar", "paper_count": 3},
    {"name": "Jennifer Brown", "paper_count": 2}
  ],
  "network_size_category": "large",
  "diversity_score": 8.5,
  "interpretation": "Excellent collaboration network with 24 unique co-authors. Balanced between 5 core collaborators and diverse author pool. Papers span multiple institutions, indicating strong inter-institutional research partnerships. Demonstrates ability to build and maintain productive research teams.",
  "timestamp": "2024-12-01T10:40:00Z"
}
```

### 10.3 Overall Candidate Summary

**Generated HTML Report Summary**:
```
OVERALL EVALUATION: Dr. Sarah Chen

Overall Score: 88/100
Overall Grade: EXCELLENT

┌─ Module Breakdown ─────────────────────────────┐
│ Education:                92/100 (25%) EXCELLENT│
│ Research:                92/100 (35%) EXCELLENT │
│ Experience:              88/100 (20%) EXCELLENT │
│ Skills Alignment:        82/100 (10%)   GOOD    │
│ Topic Variability:       7.2/10  (5%)  SPECIALIST
│ Collaboration:           8.5/10  (5%)   EXCELLENT
└───────────────────────────────────────────────┘

CANDIDATE PROFILE:
Dr. Sarah Chen is an outstanding faculty candidate with a strong research record and 
clear academic trajectory. She holds a PhD from Carnegie Mellon University (top-5 
institution) with exceptional academic performance (98% GPA). Her research profile 
is exceptional: 20 publications with 15 as first author, predominantly in top-tier 
venues (Q1/A*). She demonstrates strong leadership through supervision of 5 students 
(2 PhD, 3 MS) and collaboration with 24+ co-authors across institutions.

STRENGTHS:
+ PhD from elite institution (CMU, rank 32)
+ Excellent academic performance across education levels
+ Strong publication record in top-tier journals and conferences
+ Clear research specialization (Efficient Neural Architectures, NLP)
+ Demonstrated research team leadership
+ Excellent collaboration network across institutions
+ Industry + academia balanced experience

AREAS FOR DEVELOPMENT:
- No book publications or patents (not essential but could strengthen profile)
- Limited teaching experience documentation (current role is first faculty position)
- Topic focus has shifted; some potential for broader exploration

RECOMMENDATIONS:
✓ STRONG FIT for faculty position in Computer Science/AI
✓ Recommend for interview stage
✓ Consider for research-intensive role

MISSING INFORMATION:
- Teaching philosophy statement (not found in CV)
- Diversity and inclusion engagement (not documented)
- Professional service roles (conference organization, committee work)

Follow-up email has been drafted for information completion.
```

### 10.4 Web Dashboard Display

**Candidates List Page**:
```
┌─────────────────────────────────────────────────────────────────────┐
│ Processed Candidates (15 total)                      [Filter] [Sort] │
├─────────────────────────────────────────────────────────────────────┤
│ Name                │ Email              │ Score │ Grade      │ ...  │
├─────────────────────────────────────────────────────────────────────┤
│ Dr. Sarah Chen      │ s.chen@uni.edu    │  88   │ EXCELLENT  │ View │
│ Prof. James Wilson  │ j.wilson@uni.edu  │  82   │ EXCELLENT  │ View │
│ Dr. Maria Garcia    │ m.garcia@uni.edu  │  76   │ GOOD       │ View │
│ Dr. Ahmed Hassan    │ a.hassan@uni.edu  │  68   │ GOOD       │ View │
│ ...                 │ ...                │  ...  │ ...        │ ...  │
└─────────────────────────────────────────────────────────────────────┘
```

**Candidate Detail Page (Visual Layout)**:
```
┌──────────────────────────────────────────────────────────────────┐
│ Dr. Sarah Chen                                    ✓ EXCELLENT   │
│ Email: s.chen@university.edu | Phone: +1-555-123-4567          │
├──────────────────────────────────────────────────────────────────┤
│ OVERALL SCORE: 88/100                                   [CHART]  │
│                                                                  │
│ Module Weights:                                                 │
│ ████████████░░░ Education      25% (92/100)        EXCELLENT   │
│ █████████████░░ Research       35% (92/100)        EXCELLENT   │
│ ██████░░░░░░░░░ Experience    20% (88/100)         EXCELLENT   │
│ ████░░░░░░░░░░░ Skills         10% (82/100)           GOOD     │
│ ██░░░░░░░░░░░░░ Topic Var      5% (7.2/10)       SPECIALIST   │
│ ██░░░░░░░░░░░░░ Collaboration  5% (8.5/10)        EXCELLENT   │
├──────────────────────────────────────────────────────────────────┤
│ EDUCATION SECTION                                                │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ PhD Computer Science | Carnegie Mellon University (2012)   │ │
│ │ GPA: 3.92/4.0 (98%) | QS Rank: 32 (Tier 1)                │ │
│ │                                                              │ │
│ │ BS Computer Engineering | UC Berkeley (2008)               │ │
│ │ GPA: 3.85/4.0 (96%) | QS Rank: 10 (Tier 1)                │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ Education Score: 95/100 [EXCELLENT]                            │
├──────────────────────────────────────────────────────────────────┤
│ EXPERIENCE SECTION                                               │
│ ─── 2018-Present ────────────────────────────────────────────   │
│ Associate Professor | Tech University                           │
│ "Lead AI research group, teach algorithms/distributed systems"  │
│                                                                  │
│ ─── 2015-2018 ───────────────────────────────────────────────   │
│ Senior Research Scientist | Google Research                     │
│ "Developed neural networks for NLP; Published 8 papers"         │
├──────────────────────────────────────────────────────────────────┤
│ PUBLICATIONS (20 total)                                          │
│                                                                  │
│ Journals (8):                                                   │
│ • Q1 [WoS] Efficient Transformer Architectures... (2022)       │
│ • Q1 [WoS] Neural Network Optimization... (2021)               │
│ ... [more papers]                                               │
│                                                                  │
│ Conferences (12):                                               │
│ • A* [ICML] Attention is Not Enough... (2021)                  │
│ • A [NeurIPS] Recurrent Neural Networks... (2020)              │
│ ... [more papers]                                               │
├──────────────────────────────────────────────────────────────────┤
│ SUPERVISED STUDENTS                                              │
│ • Michael Zhang (PhD, 2023) — [Main Advisor]                   │
│ • Lisa Wang (PhD, in progress) — [Main Advisor]                │
│ • James Patel (MS, 2023) — [Main Advisor]                      │
├──────────────────────────────────────────────────────────────────┤
│ SKILLS & ALIGNMENT                                               │
│ • Python ✓ Strong (CV + publications + teaching)               │
│ • Machine Learning ✓ Strong (8+ pubs, Google role)            │
│ • TensorFlow ◐ Partial (publications, not job desc)            │
│ • Natural Language Processing ✓ Strong (research focus)        │
│ • Research Leadership ✓ Strong (team lead, supervision)        │
│                                                                  │
│ Skill Alignment Score: 82/100 [EXCELLENT]                      │
└──────────────────────────────────────────────────────────────────┘
```

---

## 11. Limitations

### 11.1 Technical Limitations

1. **PDF Parsing Constraints**:
   - Scanned/image-based PDFs: PyMuPDF cannot extract text from image PDFs (requires OCR, not implemented)
   - PDF password-protected documents: Cannot process without password
   - Unusual PDF formats: Complex layouts, embedded objects, or non-standard text encoding may fail

2. **LLM Extraction Accuracy**:
   - No supervised fine-tuning: Uses general-purpose LLMs without domain-specific training
   - Hallucination risk: LLM may invent publications, affiliations, or dates despite prompt engineering
   - Context length: Large CVs (>4000 tokens) may be truncated; information loss
   - Language dependency: Optimized for English CVs; non-English CVs will have lower accuracy

3. **External Data Source Limitations**:
   - QS Rankings: Covers only ~1200 universities; most institutions are unranked (defaulting to Tier 3)
   - Scimago/CORE: Annual updates; may miss recently launched journals or conferences
   - Publication APIs (CrossRef, OpenAlex): API rate limits, occasional outages, incomplete coverage
   - Journal metadata: Some journals/conferences have missing or incorrect ISSN/ranking data

4. **Scoring Model Limitations**:
   - Fixed weights: Education 25%, Research 35%, Experience 20%, Skills 10%, Variability 5%, Collaboration 5% (uniform across all candidates; doesn't account for field-specific variation)
   - No context awareness: Scores don't account for candidate's career stage, field, institution, or geographic region
   - Publication quality metric: Only considers journal quartile and conference rank; doesn't account for citation count, h-index, or recent impact
   - Country bias: QS/Scimago rankings favor Western institutions; underrepresents quality institutions in developing countries

5. **Database Constraints**:
   - Single-tenant assumption: No user authentication, access control, or multi-organization support
   - No audit trail: Cannot track who viewed or evaluated which candidate
   - Text field length: Large CV text or descriptions are truncated at DB column limits

### 11.2 Functional Limitations

1. **No Job Description Matching**:
   - System doesn't parse job requirements; scores are generic faculty-hiring criteria
   - Cannot customize evaluation for specific positions (e.g., "AI specialist" vs. "systems researcher")

2. **Limited Context Integration**:
   - Doesn't consider candidate's research statement, teaching philosophy, or cover letter
   - No integration with external sources (LinkedIn, Google Scholar, ResearchGate profiles)
   - Cannot verify candidate claims or detect conflicts of interest

3. **No Interview/Assessment Integration**:
   - System only evaluates CV; doesn't incorporate interview scores, reference checks, or teaching evaluations
   - Cannot track hiring decisions or outcomes (offer accepted, candidate started, performance feedback)

4. **Email Functionality**:
   - Email generation is rule-based with LLM templates; doesn't adapt to individual candidate contexts
   - No email tracking or confirmation of receipt
   - SMTP configuration is manual; no cloud email service integration

5. **Visualization Constraints**:
   - Dashboard is static; cannot drill down into publication details without manual file review
   - No network visualization for collaboration graphs
   - Limited comparison views (max 2-3 candidates side-by-side)

### 11.3 Operational Limitations

1. **Processing Performance**:
   - Sequential CV processing: One CV at a time; N CVs take ~2-5 minutes each depending on LLM provider
   - No caching of scoring results: Re-processing same CV re-calculates all scores (slow but fresh)
   - PDF extraction: Large PDFs (>50 pages) may timeout or use significant memory

2. **Data Security & Privacy**:
   - CVs stored in plaintext in database; no encryption at rest
   - No data deletion workflow; candidate records persist indefinitely
   - No HIPAA/GDPR compliance; not suitable for regulated industries
   - API keys stored in .env file; no secrets management

3. **Scalability**:
   - Single Redis instance: No clustering or failover for cache
   - PostgreSQL: No read replicas or connection pooling optimization
   - Frontend: Single-page app; all candidates loaded at once (slow for 1000+ candidates)
   - No background job queue: Scoring blocks API response

4. **Maintenance**:
   - CSV dataset updates: Requires manual file replacement (no automatic updates)
   - LLM model changes: Hardcoded model names; requires code change to update models
   - Dependency management: No version pinning; potential breaking changes in libraries

### 11.4 Bias & Fairness Limitations

1. **Institutional Bias**:
   - QS rankings favor Anglo-American universities; non-ranked institutions (especially in developing countries) are penalized
   - No consideration for institution's recent improvements or regional prestige

2. **Publication Bias**:
   - English-language journals dominate rankings; non-English publications are undervalued
   - Conference metrics don't account for regional prestige (e.g., strong local conferences outside CORE ranking)
   - Early-career researchers naturally have fewer publications; scoring penalizes young candidates

3. **Demographic Bias**:
   - No fairness checks for gender, race, or national origin
   - Name-based screening might introduce bias if embedded in LLM
   - Career gap interpretation (e.g., for caregiving) not explicitly handled

4. **Field-Specific Bias**:
   - Scoring assumes computer science/STEM norms (publication quantity, conference prestige)
   - Humanities/social sciences have different publication patterns (books > journals); would score lower unfairly
   - Professional experience weight (20%) may undervalue pure researchers from industry

---

## 12. Future Work

### 12.1 Short-Term Enhancements (3-6 months)

1. **OCR for Image PDFs**:
   - Integrate Tesseract or EasyOCR for scanned CV processing
   - Expand usability to candidates submitting image-based PDFs

2. **Publication Citation Tracking**:
   - Query Google Scholar or Semantic Scholar for citation counts
   - Incorporate h-index and citation impact into research scoring
   - Track publication growth trajectory over time

3. **Job Description Parsing**:
   - Add optional job description upload
   - Parse required skills, experience, qualifications using LLM
   - Score candidate alignment to specific role (vs. generic faculty criteria)

4. **Enhanced Email System**:
   - Integrate with Gmail/Office 365 API for actual sending (vs. draft generation)
   - Track email open rates and responses
   - Auto-remind for follow-ups

5. **Improved Scoring Explainability**:
   - Generate evidence citations for each score component
   - Show which publications/experiences contributed to score
   - Allow hiring committee to adjust weights dynamically

### 12.2 Medium-Term Features (6-12 months)

1. **Research Profile Visualization**:
   - Interactive publication timeline showing research evolution
   - Co-author network graph (force-directed graph visualization)
   - Topic evolution sankey diagram (showing theme transitions over time)
   - Citation trend chart

2. **Candidate Comparison Dashboard**:
   - Side-by-side comparison of 3-5 candidates
   - Radar chart showing module-by-module strengths
   - Candidate ranking with user-defined weights
   - Export comparison as PDF report

3. **Hiring Workflow Integration**:
   - Candidate status tracking (pipeline stages: screened, interviewed, offered, hired)
   - Hiring committee feedback and scoring system
   - Interview notes and decision documentation
   - Outcome tracking (hired, rejected, offer declined)

4. **Multi-Position Support**:
   - Create multiple job openings with custom criteria
   - Match candidates to best-fit positions automatically
   - Compare candidates across positions

5. **Data Privacy Features**:
   - GDPR/CCPA-compliant data deletion (right-to-be-forgotten)
   - Encryption at rest (database-level or application-level)
   - Data retention policies
   - Access audit logs

### 12.3 Long-Term Roadmap (1-2 years)

1. **Multi-Language Support**:
   - Support CVs in Spanish, Mandarin, French, German, etc.
   - Automatic language detection and translation
   - Localized institution ranking datasets

2. **Advanced LLM Capabilities**:
   - Fine-tune LLM on institutional CV extraction (domain adaptation)
   - Integrate multimodal LLMs (handle CV images, embedded charts)
   - Few-shot learning from manually-annotated CVs

3. **Research Impact Assessment**:
   - Integration with Scopus, WoS, and Google Scholar for citation metrics
   - Patent impact assessment (number of citations, commercial applications)
   - Research trending topics and contribution to emerging fields

4. **Diversity & Inclusion Analytics**:
   - Fairness audit: detect and mitigate gender, race, geographic bias in scoring
   - Diversity metrics dashboard (gender, international, underrepresented groups)
   - Recommendations for balanced hiring

5. **Candidate Recommendation Engine**:
   - ML-based matching: predict which candidates are likely to succeed
   - Early warning system: identify candidates at risk of attrition
   - Predict candidate quality based on CV features vs. hiring outcomes

6. **Enterprise Features**:
   - Multi-organization/university support
   - Role-based access control (hiring manager, recruiter, faculty committee)
   - Bulk operations (batch candidate uploads, bulk email)
   - API for third-party HR system integration

7. **Predictive Hiring Outcomes**:
   - Collect hiring outcomes (hired, success metrics, retention)
   - Build regression model: predict candidate success based on CV features
   - Continuous learning: improve scoring weights based on outcomes

### 12.4 Research Opportunities

1. **Bias Mitigation in LLM Extraction**:
   - Study: How do different prompt framings affect demographic fairness?
   - Develop bias-aware prompting strategies
   - Publish fairness paper in NLP/HCI venue

2. **Publication Quality Metrics**:
   - Investigate: Do current ranking methods (Q1, CORE) align with actual research impact?
   - Develop alternative quality metrics based on citation patterns
   - Compare field-specific ranking methodologies

3. **Career Trajectory Prediction**:
   - Dataset: Collect outcomes (hired, promoted, citations, retention) for evaluated candidates
   - Model: Predict career success from CV features
   - Publish in ML/econometrics venue

4. **Prompt Engineering for Structured Extraction**:
   - Benchmark different extraction prompts across CV formats
   - Develop domain-specific extraction guidelines
   - Quantify improvements from schema-based (Pydantic) vs. free-form extraction

---

## Conclusion

TALASH demonstrates the practical application of Large Language Models to a real-world problem: fairness and efficiency in academic hiring. By automating CV processing and providing structured, multi-dimensional evaluation, the system reduces bias, improves scalability, and accelerates hiring decisions while maintaining transparency and explainability.

The project showcases:
- **LLM Integration**: Production-grade multi-provider fallback system with error handling
- **Data Engineering**: Complex extraction, normalization, and scoring across structured and unstructured data
- **Full-Stack Development**: React frontend, FastAPI backend, PostgreSQL database, Redis caching
- **Software Engineering**: Async processing, database schema design, error handling, testing

Future iterations can build on this foundation to add fairness auditing, hire-outcome prediction, and enterprise features while continuously improving the accuracy and explainability of candidate evaluation.

---

**Document Version**: 1.0  
**Last Updated**: May 10, 2026  
**Author**: [Full-Stack Development Team]  
**Course**: CS417 - Large Language Models  

