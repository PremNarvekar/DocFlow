# DOCFLOW_00_ENGINEERING_AUDIT

## 1. Executive Summary
DocFlow is currently in a "prototype" state. It features a genuinely excellent, well-designed AI abstraction layer (router, registry, normalized error handling). However, the rest of the application is extremely naive. It processes entire PDF documents synchronously in the FastAPI web thread, stores unbounded text in ChromaDB without chunking, and lacks asynchronous workers, deployment configuration, and proper observability. It works for offline tests, but would catastrophically fail in a production environment under any real load.

## 2. Repository Structure
The codebase is split into `backend/` and `frontend/`. 
- `backend/ai/`: Strong multi-provider abstraction layer.
- `backend/pipeline/`: Synchronous document processing logic.
- `backend/models/`: Pydantic data schemas.
- `backend/tests/`: Extensive offline test suite.
- Placeholder files (`Dockerfile`, `docker-compose.yml`, `tasks.py`, `.github/workflows/deploy.yml`) exist but contain 0 bytes.

## 3. Current Architecture
A single FastAPI application (`main.py`) acts as a monolith. When a request arrives, the server halts its HTTP thread to run PyMuPDF extraction, send API requests to AI providers, validate Pydantic output, run deterministic anomaly checks, and finally write to ChromaDB.

## 4. Current Request Flow
1. Client -> `POST /documents`
2. Save uploaded PDF to a temporary file.
3. `load_and_extract` (PyMuPDF extracts all text).
4. `classify_document` (First 1,000 chars sent to AI).
5. `extract_document` (100% of the document text sent to AI).
6. Deterministic Anomaly Detection (`anomaly.py`).
7. `store.add_document` (Entire text saved to ChromaDB).
8. Client receives processed JSON.

## 5. Current AI Architecture
Highly defensible. It uses an `AIProvider` abstract base class enforcing `generate()` and `parse()`. A `ProviderRegistry` checks `.env` configuration safely. An `AIRouter` handles fallback sequences across providers based on an `ErrorCategory` enum mapping (retrying on 429s/500s, failing fast on 401s).

## 6. Current Document Pipeline
Dangerously naive. It relies on passing an unbounded string (`\n{text}`) to the LLM. There is no chunking, no mapping/reducing, and no page isolation. Large documents will instantly trigger `TokenLimit` or memory exhaustion exceptions.

## 7. Current Storage Architecture
ChromaDB is instantiated locally in `./chroma_db`. It stores the *entire document* as a single record (`documents=[text]`). Without semantic chunking, embeddings represent the statistical average of a whole document, rendering vector search entirely useless for specific factual retrieval (RAG).

## 8. Current API Architecture
A single FastAPI application with only two endpoints: `GET /health` and `POST /documents`. It handles file uploads efficiently but poorly manages concurrency by keeping the TCP connection open during massive LLM delays.

## 9. Current Async Architecture
**NOT IMPLEMENTED.** `tasks.py` is a 0-byte file. The system processes everything synchronously.

## 10. Current Testing Architecture
Good offline coverage. `tests/test_ai_providers.py` extensively tests the router, fallback behavior, and structured output using `MockProvider`. Real API tests exist but fail due to credential issues.

## 11. Current Deployment Architecture
**NOT IMPLEMENTED.** `Dockerfile`, `docker-compose.yml`, and `.github/workflows/deploy.yml` are 0-byte placeholders.

## 12. Current Observability
**NOT IMPLEMENTED.** `print()` statements and standard Python exceptions. No structured JSON logging, no token/cost tracking, and no LangSmith integration. 

## 13. Current Security Posture
**PARTIALLY IMPLEMENTED.** Uses `.env` for secrets, which is good. Does not log API keys. However, it treats the uploaded PDF content entirely as trusted text. There is no defense against Prompt Injection within the document. File validation exists (MIME `.pdf` check), but it does not sanitize file names completely or check for malicious logic bombs.

## 14. Current Provider Status
- **Gemini**: CONFIGURED BUT AUTH FAILED (Invalid 53-character key string).
- **xAI / Grok**: NOT CONFIGURED.
- **Groq**: NOT CONFIGURED.
- **Cerebras**: NOT CONFIGURED.
- **Mistral**: NOT CONFIGURED.
- **OpenRouter**: NOT CONFIGURED.
- **Mock Provider**: WORKING — STRUCTURED OUTPUT VERIFIED.

## 15. Known Bugs
- The `GEMINI_API_KEY` placeholder causes an active `401 UNAUTHENTICATED` when integration tests attempt real calls.
- `extractor.py` has no size limitation, inevitably crashing on large files.

## 16. Architectural Weaknesses
- Synchronous processing blocks ASGI workers.
- No chunking limits vector search effectiveness.
- Centralizing logic in `main.py` violates single-responsibility patterns.

## 17. Technical Debt
- Empty placeholder files everywhere.
- Missing configuration validation at startup (if `.env` is empty, it just lets all models silently drop to "unavailable" rather than warning the operator).

## 18. Production Risks
- OOM (Out of Memory) crashes due to loading huge PDFs fully into memory.
- Unbounded LLM costs due to sending entire raw documents into prompts.
- Web server connection timeouts on documents that take >30 seconds to process.

## 19. Missing Capabilities
- Async Queue (Celery/Redis).
- Containerization (Docker).
- Real Cross-Document RAG retrieval.
- Token and Cost Tracking.
- Structured Logging.

## 20. Recommended Target Architecture
- **API**: FastAPI (`/documents` returns `202 Accepted` + `job_id`).
- **Queue**: Redis Message Broker.
- **Workers**: Celery cluster.
- **Pipeline**: PDF -> PyMuPDF Page Generator -> Semantic Chunking -> AI Classifier -> AI Extractor (via Router) -> Pydantic -> Anomaly Check -> Chunked ChromaDB.
- **Monitoring**: Structured logging with Request IDs, token counting.

## 21. Recommended Implementation Order
1. Phase 1: Official API Research (Gemini, Grok, HuggingFace).
2. Phase 2-4: Upgrade Gemini, Grok, and HF integrations securely.
3. Phase 5-6: Upgrade the Router with advanced task-based prioritization.
4. Phase 7-12: Hardened Document Pipeline (Chunking, Safe Extraction, Deterministic validation).
5. Phase 13-16: Chunked Storage and true RAG.
6. Phase 17: Async Architecture (Celery/Redis).
7. Phase 18-31: Observability, Docker, Security, API cleanup.

## 22. Files that must change
- `main.py`, `tasks.py`, `pipeline/loader.py`, `pipeline/classifier.py`, `pipeline/extractor.py`, `pipeline/store.py`, all `ai/providers/*.py` files.

## 23. Files that should remain unchanged
- Pydantic models in `models/*.py` (business domain is solid).
- The abstract interfaces `ai/base.py` and `ai/registry.py` (architecturally sound).

## 24. High-risk changes
- Rewriting the synchronous pipeline into an asynchronous Celery workflow is a massive architectural shift that will break the current `POST /documents` contract.
- Changing `store.py` to support chunks means the database schema/metadata must be completely overhauled.

## 25. Interview weaknesses
- "Why did you use Vector Search without chunking?" (Shows lack of ML/NLP understanding).
- "How does your FastAPI app handle 10 concurrent 20-second PDF uploads?" (It doesn't, it crashes. Shows lack of web concurrency understanding).

## 26. Architect-level weaknesses
- Relying on the LLM's context window instead of MapReduce/chunking shows poor cost management and performance engineering.
- Missing correlation IDs makes tracing a failed extraction back to a specific file in production impossible.

## 27. Questions that need verification
- What is the exact 2026 syntax for Gemini 3.1 Pro Preview's structured output?
- Does xAI currently support strict JSON schemas or only JSON mode?
- Which Hugging Face Inference endpoint provides the best reliable structured JSON generation for extraction tasks?
