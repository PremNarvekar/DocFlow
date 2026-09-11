# DOCFLOW_01_AI_PROVIDER_RESEARCH

## 1. Google Gemini (Primary Provider)

### 1.1 SDK and Authentication
**WHAT**: Use the official `google-genai` Python SDK. Authentication via `api_key` passed to `genai.Client()`.
**WHY**: Google deprecated the legacy `google-generativeai` SDK. The new `google-genai` SDK is the unified interface for Gemini APIs and provides first-class support for Pydantic schemas.
**HOW**: `client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))`
**ALTERNATIVES**: Direct REST API calls or LangChain.
**WHY ALTERNATIVE WAS NOT USED**: Direct REST requires building complex retry and streaming wrappers. LangChain adds unnecessary abstraction and breaking changes.
**TRADEOFF**: Dependency on Google's SDK release cycles.
**PRODUCTION IMPACT**: Cleaner code, automatic payload validation, and native Pydantic integrations.
**INTERVIEW QUESTION**: "Why did you choose the `google-genai` SDK over REST or LangChain?"

### 1.2 Model Selection
**WHAT**: `gemini-3.1-pro-preview` for complex extraction/reasoning; `gemini-2.5-flash` for classification/simple tasks.
**WHY**: 3.1 Pro provides a massive 2M+ context window and native document understanding (PDF). Flash provides sub-second latency for simple routing.
**HOW**: Configured via environment variables with hardcoded fallbacks.

### 1.3 Structured Output
**WHAT**: Pass Pydantic models directly to `response_schema` in `GenerateContentConfig`.
**WHY**: Gemini natively enforces the schema on the backend, preventing syntax hallucinations.
**HOW**: 
```python
config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=InvoiceData,
)
```
**ALTERNATIVES**: Asking the model to "output JSON" and parsing it manually.
**WHY ALTERNATIVE WAS NOT USED**: Unreliable. The model might output markdown code blocks or invalid JSON. Native schema enforcement guarantees structural correctness.
**TRADEOFF**: Complex recursive Pydantic structures or exotic types (e.g., Decimal) might require simplification to standard JSON types (float/str).

### 1.4 Native Document Processing (PDF)
**WHAT**: We will evaluate Gemini's native File API (`client.files.upload`) for multimodal PDF ingestion vs. PyMuPDF text extraction.
**WHY**: Gemini can "see" layouts, tables, and signatures that PyMuPDF flattens or destroys. 
**TRADEOFF**: Uploading files to Google introduces latency and state management (waiting for the file to process, cleaning it up).

---

## 2. xAI / Grok (Secondary / Fallback Provider)

### 2.1 SDK and Authentication
**WHAT**: Use the official `openai` Python SDK pointing to `https://api.x.ai/v1`.
**WHY**: xAI officially recommends the OpenAI compatibility layer.
**HOW**: `client = AsyncOpenAI(api_key=XAI_KEY, base_url="https://api.x.ai/v1")`
**ALTERNATIVES**: Writing a custom HTTP client for xAI.
**WHY ALTERNATIVE WAS NOT USED**: Reinventing the wheel; the OpenAI SDK is heavily battle-tested, handles connection pooling, and manages timeout/retries natively.
**PRODUCTION IMPACT**: Zero learning curve, proven stability, and native async support.

### 2.2 Model Selection
**WHAT**: `grok-3-mini` (or latest fast variant) as a fallback for Flash, and `grok-3` for Pro.
**WHY**: Provides comparable reasoning to tier-1 models while maintaining API compatibility.

### 2.3 Structured Output
**WHAT**: Use JSON mode (`response_format={"type": "json_object"}`) alongside strict system instructions detailing the Pydantic schema structure.
**WHY**: While OpenAI supports strict schema parsing (`.parse()`), xAI's compatibility layer guarantees JSON mode but may not fully support the strict schema constraint API natively.
**HOW**: Serialize the Pydantic model's `model_json_schema()` into the system prompt and enforce JSON mode.

---

## 3. Hugging Face (Open-Source Fallback)

### 3.1 SDK and Authentication
**WHAT**: Use `huggingface_hub` and `InferenceClient`.
**WHY**: It's the official, lightweight SDK for querying serverless Inference Endpoints without requiring a massive local GPU or the heavy `transformers` library.
**HOW**: `client = InferenceClient(api_key=HF_TOKEN)`

### 3.2 Model Selection
**WHAT**: `meta-llama/Meta-Llama-3-70B-Instruct` (or latest 8B/70B variants).
**WHY**: Llama 3 models have proven exceptional at instruction following and JSON generation, making them the most reliable open-source fallback for data extraction.
**ALTERNATIVES**: Running local models via Ollama.
**WHY ALTERNATIVE WAS NOT USED**: Local models require dedicated GPU hardware for production, massively increasing infrastructure costs compared to remote serverless endpoints.

### 3.3 Structured Output
**WHAT**: Hugging Face Inference API supports text generation but structured output relies heavily on prompt engineering or grammar constraints (if the specific backend supports it).
**WHY**: We need to treat HF as a generic text-in/text-out interface and strictly validate with Pydantic post-generation.
**PRODUCTION IMPACT**: Higher likelihood of `ValidationError` compared to Gemini. The Router must gracefully handle `INVALID_RESPONSE` errors from HF.

---

## 4. Universal Error Handling Strategy

### 4.1 Normalization
**WHAT**: Map SDK-specific errors to `ErrorCategory`.
**HOW**:
- `google.genai.errors.ClientError (429)` -> `RATE_LIMITED`
- `openai.RateLimitError` -> `RATE_LIMITED`
- `huggingface_hub.utils.HfHubHTTPError (503)` -> `SERVER_ERROR`
**WHY**: The Router must not care *which* provider failed, only *how* it failed, to apply the correct retry logic.
