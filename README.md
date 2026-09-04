# DocFlow

### Document Intelligence for Business Workflows

DocFlow turns unstructured business documents into structured, searchable data.

A user can upload an invoice, contract, medical report, or financial statement. DocFlow identifies the document type, extracts the important information using Gemini and Pydantic, validates the data, detects anomalies, stores the document for semantic search, and lets users ask questions about their documents using natural language.

The goal is not just to extract text from PDFs.

The goal is to turn documents into **data that can actually be used by an application**.

---

# The Problem

A lot of business information is still locked inside PDFs.

For example, an invoice may contain:

* Vendor information
* Customer information
* Line items
* Taxes
* Payment terms
* Total amount

A contract may contain:

* Parties
* Effective dates
* Contract value
* Payment terms
* Termination conditions

A financial statement may contain:

* Revenue
* Expenses
* Profit
* Assets
* Liabilities
* Cash flow

A traditional document workflow often looks like this:

```text
PDF
 ↓
Human reads the document
 ↓
Human searches for the required information
 ↓
Human copies the information into another system
 ↓
Human checks for errors
 ↓
Human stores the document
```

This process is slow, repetitive, and difficult to scale.

DocFlow changes the workflow to:

```text
PDF
 ↓
Automated processing
 ↓
Document classification
 ↓
Structured extraction
 ↓
Validation
 ↓
Anomaly detection
 ↓
Semantic indexing
 ↓
Natural-language queries
```

---

# What DocFlow Does

DocFlow currently supports four document types:

| Document Type       | Example Information                                     |
| ------------------- | ------------------------------------------------------- |
| Invoice             | Invoice number, vendor, customer, items, tax, total     |
| Contract            | Parties, dates, value, payment terms, termination terms |
| Medical Report      | Patient information, tests, results, findings           |
| Financial Statement | Revenue, expenses, profit, assets, liabilities          |

Each document type has its own Pydantic schema.

This is intentional.

An invoice and a contract have very different structures, so forcing both into one generic schema would make the extraction layer less reliable and harder to maintain.

Instead:

```text
Invoice       → InvoiceData
Contract      → ContractData
Medical       → MedicalReportData
Financial     → FinancialStatementData
```

This also makes it easier to add or change document types later.

---

# Architecture

```text
                         ┌─────────────────────┐
                         │      React UI       │
                         │                     │
                         │ Upload / Query / UI  │
                         └──────────┬──────────┘
                                    │
                                   HTTP
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      FastAPI        │
                         │        API          │
                         └──────────┬──────────┘
                                    │
                                Create Job
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Redis / Queue    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Celery Worker     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Document Loader   │
                         │      PyMuPDF        │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Classifier       │
                         │       Gemini        │
                         └──────────┬──────────┘
                                    │
                       ┌────────────┴────────────┐
                       │                         │
                       ▼                         ▼
                InvoiceData                ContractData
                MedicalData                FinancialData
                       │                         │
                       └────────────┬────────────┘
                                    ▼
                         ┌─────────────────────┐
                         │ Structured          │
                         │ Extraction          │
                         │ Gemini + Pydantic   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Anomaly Detection   │
                         │   Business Rules    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      ChromaDB       │
                         │ Embeddings +        │
                         │ Metadata            │
                         └──────────┬──────────┘
                                    │
                             Natural Language
                                  Query
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Retrieval + Gemini  │
                         │        RAG          │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Answer + Sources    │
                         │ Document + Page     │
                         └─────────────────────┘
```

---

# End-to-End Data Flow

## 1. Upload

The user uploads a PDF through the React frontend.

```text
User
 ↓
FileUploader
 ↓
POST /upload
 ↓
FastAPI
```

The API does not process the entire document inside the HTTP request.

Instead, it creates a processing job and returns a `job_id`.

```json
{
  "job_id": "abc123",
  "status": "queued"
}
```

This keeps the API responsive while the document is processed in the background.

---

# 2. Asynchronous Processing

The job is sent to Redis and picked up by a Celery worker.

```text
FastAPI
   ↓
Redis
   ↓
Celery Worker
```

This is important because document processing can take longer than a normal API request.

Instead of keeping the user waiting for the HTTP request to finish, the API creates the job and lets the worker handle the processing independently.

---

# 3. PDF Extraction

PyMuPDF loads the document page by page.

```text
document.pdf
     ↓
PyMuPDF
     ↓
Page 1 → text
Page 2 → text
Page 3 → text
...
```

Page information is kept during extraction because it is needed later when showing the source of an answer.

For example:

```json
{
  "file_name": "invoice.pdf",
  "page_count": 3,
  "pages": [
    {
      "page_num": 1,
      "text": "..."
    },
    {
      "page_num": 2,
      "text": "..."
    }
  ]
}
```

---

# 4. Document Classification

DocFlow sends a small preview of the extracted text to Gemini to identify the document type.

```text
Extracted Text
      ↓
First ~500 characters
      ↓
Gemini
      ↓
DocumentType
```

Supported types are:

```text
invoice
contract
medical_report
financial_statement
unknown
```

If the document does not match a supported type, it is marked as `unknown` instead of being forced into the wrong category.

---

# 5. Structured Extraction

The document type determines which Pydantic schema is used.

```text
invoice
    ↓
InvoiceData

contract
    ↓
ContractData

medical_report
    ↓
MedicalReportData

financial_statement
    ↓
FinancialStatementData
```

Gemini is used for structured extraction.

The result is then validated with Pydantic.

```text
Gemini
 ↓
Structured JSON
 ↓
Pydantic validation
 ↓
Application data
```

This creates a clear boundary between model-generated output and application logic.

Gemini is responsible for extracting the information.

Pydantic is responsible for checking that the returned data follows the expected structure.

---

# 6. Anomaly Detection

Extracting information is only part of the problem.

DocFlow also checks the extracted data against business rules.

For example:

```text
Duplicate invoice number
        ↓
HIGH

Missing required field
        ↓
MEDIUM

Unusually large amount
        ↓
HIGH

Potentially suspicious value
        ↓
LOW / MEDIUM / HIGH
```

An anomaly can look like this:

```json
{
  "anomaly_type": "duplicate_invoice",
  "severity": "high",
  "message": "Invoice INV-1042 already exists."
}
```

These checks are handled by deterministic business rules rather than another LLM prompt.

The basic separation is:

```text
LLM
 ↓
Extract information

Application
 ↓
Validate information
 ↓
Apply business rules
 ↓
Detect anomalies
```

This makes the system easier to test and reason about.

---

# 7. Vector Storage

After the document is processed, its text is split into chunks and indexed.

```text
Document
 ↓
Pages
 ↓
Chunks
 ↓
Embeddings
 ↓
ChromaDB
```

Each chunk keeps useful metadata:

```json
{
  "document_id": "abc123",
  "file_name": "invoice.pdf",
  "document_type": "invoice",
  "page": 2
}
```

Keeping this metadata with each chunk makes it possible to return the source document and page with the final answer.

---

# 8. Natural-Language Queries

Users can ask questions about their documents in normal language.

For example:

> Which vendor charged the most this month?

The query flow is:

```text
User Question
      ↓
Embedding
      ↓
ChromaDB similarity search
      ↓
Relevant document chunks
      ↓
Metadata
      ↓
Gemini
      ↓
Answer
      ↓
Source document + page
```

Example response:

```text
Answer:

ABC Supplies had the highest invoice total at ₹425,000.

Sources:

invoice_aug_12.pdf — Page 2
invoice_aug_18.pdf — Page 1
```

This turns the document collection from a simple file archive into a searchable knowledge base.

---

# Engineering Decisions

## Specialized Schemas

Instead of using one schema for every document type, DocFlow uses separate schemas:

```text
Invoice       → InvoiceData
Contract      → ContractData
Medical       → MedicalReportData
Financial     → FinancialStatementData
```

This keeps each document type independent and makes the system easier to extend.

---

## Async Processing

Large documents can take much longer to process than a normal API request.

A simple synchronous approach would look like:

```text
POST /upload
      ↓
Process PDF
      ↓
Call Gemini
      ↓
Generate embeddings
      ↓
Return response
```

DocFlow instead uses:

```text
POST /upload
      ↓
Create job
      ↓
Return job_id
```

While the worker handles the actual processing:

```text
Celery Worker
      ↓
Process document
```

This keeps the API responsive and separates request handling from heavy processing.

---

# Performance

Performance numbers should be measured, not guessed.

DocFlow tracks the processing pipeline so we can measure things such as:

```text
Upload response latency
Classification latency
Extraction latency
Embedding latency
Total processing time
Query latency
Pages processed / second
```

The benchmark can be recorded like this:

| Metric          | Baseline | Optimized |
| --------------- | -------: | --------: |
| Upload response |      TBD |       TBD |
| Classification  |      TBD |       TBD |
| Extraction      |      TBD |       TBD |
| Full processing |      TBD |       TBD |
| Query latency   |      TBD |       TBD |

Once actual benchmarks are available, they can be added to the README.

For example, if testing shows a 32% reduction in median processing time, the project can report that measured result.

Until it has been tested, no performance number is claimed.

---

# Reliability

DocFlow is designed with clear failure points.

```text
Invalid file
     ↓
Validation error

Empty PDF
     ↓
Rejected

Unsupported document
     ↓
UNKNOWN

LLM extraction failure
     ↓
Job failure / retry

Missing field
     ↓
Validation / anomaly

Duplicate invoice
     ↓
Anomaly

Vector storage failure
     ↓
Job failure / retry
```

The goal is not to assume that AI systems never fail.

The goal is to make failures **visible, isolated, and recoverable**.

---

# Project Structure

```text
DocFlow/
│
├── backend/
│   │
│   ├── models/
│   │   ├── invoice.py
│   │   ├── contract.py
│   │   ├── medical.py
│   │   └── financial.py
│   │
│   ├── pipeline/
│   │   ├── loader.py
│   │   ├── classifier.py
│   │   ├── extractor.py
│   │   ├── anomaly.py
│   │   └── store.py
│   │
│   ├── tests/
│   │
│   ├── config.py
│   ├── tasks.py
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       └── components/
│           ├── FileUploader.jsx
│           ├── DocumentCard.jsx
│           ├── AnomalyBadge.jsx
│           ├── ProcessingQueue.jsx
│           └── NLQueryBox.jsx
│
├── .github/
│   └── workflows/
│       └── deploy.yml
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

# API

## Upload

```http
POST /upload
```

Uploads a document and creates a processing job.

Response:

```json
{
  "job_id": "abc123",
  "status": "queued"
}
```

---

## Processing Status

```http
GET /status/{job_id}
```

Example response:

```json
{
  "job_id": "abc123",
  "status": "processing",
  "progress": 65
}
```

Possible states:

```text
queued
processing
completed
failed
```

---

## Natural-Language Query

```http
POST /query
```

Example request:

```json
{
  "question": "Which vendor charged the most in August?"
}
```

Example response:

```json
{
  "answer": "...",
  "sources": [
    {
      "document": "invoice_august.pdf",
      "page": 2
    }
  ]
}
```

---

# Tech Stack

## Backend

* Python
* FastAPI
* Pydantic
* PyMuPDF
* Celery
* Redis

## AI

* Google Gemini
* Structured output
* Embeddings
* Retrieval-Augmented Generation

## Storage

* ChromaDB

## Frontend

* React
* Vite

## Infrastructure

* Docker
* Docker Compose
* GitHub Actions

---

# Running Locally

## 1. Clone the repository

```bash
git clone <repository-url>
cd DocFlow
```

## 2. Create a Python environment

```bash
cd backend

python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure environment variables

Create a `.env` file:

```text
GEMINI_API_KEY=your_api_key
```

Never commit `.env` to Git.

Use `.env.example` as the template for required environment variables.

---

# Running the Application

Start the backend:

```bash
uvicorn main:app --reload
```

Start Redis:

```bash
redis-server
```

Start the Celery worker:

```bash
celery -A tasks worker --loglevel=info
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

For the full environment, use Docker Compose:

```bash
docker compose up --build
```

---

# Testing

Run the test suite with:

```bash
pytest
```

Tests cover areas such as:

```text
PDF loading
Document classification
Structured extraction
Anomaly detection
API behavior
```

The CI pipeline runs tests before deployment.

---

# Security Considerations

DocFlow processes potentially sensitive business documents, so security needs to be considered from the beginning.

The current design follows these basic principles:

* API keys are stored in environment variables.
* `.env` files are excluded from Git.
* Uploaded documents are not committed to the repository.
* User documents are treated as untrusted input.
* File types and sizes should be validated before processing.
* Production storage should use controlled access policies.
* Medical documents used during development should be synthetic.
* Production secrets should be managed through deployment secret stores instead of source code.

For a production deployment, additional controls would be needed, including:

* Authentication
* Authorization
* Encryption at rest
* Encryption in transit
* Audit logging
* Data retention policies
* Stronger document scanning
* Role-based access control

---

# Current Limitations

DocFlow is an engineering project, not a finished enterprise document-processing platform.

Current limitations include:

* PDF text extraction does not replace a complete OCR pipeline.
* Complex tables may need layout-aware extraction.
* Classification based on a small text preview can fail on unusual documents.
* Financial calculations need deterministic validation.
* LLM extraction needs monitoring and evaluation.
* ChromaDB works well for the current project, but a managed vector database may make more sense at larger scale.
* Production deployment needs stronger authentication and data-governance controls.

These limitations are part of the current system and are areas for future improvement.

---

# Future Improvements

Potential next steps include:

```text
OCR fallback
     ↓
Layout-aware extraction
     ↓
Table extraction
     ↓
Document versioning
     ↓
Human review workflow
     ↓
Confidence scoring
     ↓
Evaluation dataset
     ↓
Observability
     ↓
Authentication / RBAC
     ↓
Production object storage
     ↓
Managed vector infrastructure
```

More document types can also be added:

```text
Purchase Orders
Receipts
Tax Documents
Shipping Documents
Insurance Documents
Bank Statements
```

The current architecture is designed so new document types can be added without rewriting the entire pipeline.

---

# What I Learned

The biggest lesson from building DocFlow is that document intelligence is not just an LLM problem.

A reliable system needs several layers working together:

```text
Document ingestion
       +
Classification
       +
Structured extraction
       +
Validation
       +
Business rules
       +
Async processing
       +
Vector retrieval
       +
API design
       +
Frontend
       +
Infrastructure
```

The LLM is one part of the system. It is not the entire system.

One of the most important boundaries in DocFlow is:

```text
Probabilistic AI
       ↓
Validation
       ↓
Deterministic application logic
```

This separation makes the system easier to test, debug, and improve.

---

# Project Status

## Core Pipeline

* PDF loading
* Page-aware text extraction
* Document classification
* Pydantic schemas
* Gemini structured extraction

## Intelligence

* Anomaly detection
* ChromaDB indexing
* Cross-document RAG
* Source attribution

## Infrastructure

* Celery + Redis
* Docker Compose
* Health checks
* Automated tests
* CI/CD
* Production deployment

## Frontend

* Multi-file upload
* Processing queue
* Document cards
* Anomaly visualization
* Natural-language query interface

---

# Why I Built It

I built DocFlow to understand what happens when an LLM is placed inside a real software system.

The interesting part is not simply asking Gemini to read a PDF.

The real challenge is building everything around the model:

```text
Unstructured input
        ↓
Reliable processing
        ↓
Structured data
        ↓
Business validation
        ↓
Async infrastructure
        ↓
Searchable knowledge
        ↓
Useful product
```

That is what I wanted to explore with this project.

**The difference between an AI demo and an AI application is everything built around the model.**
