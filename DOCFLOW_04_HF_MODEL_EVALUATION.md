# DOCFLOW_04_HF_MODEL_EVALUATION

## 1. Remote Inference vs Local GPU Strategy
**WHAT**: We will use Hugging Face Serverless Inference Endpoints via `huggingface_hub.InferenceClient` rather than downloading models locally via `transformers` or `vLLM`.
**WHY**: Hosting a 70B parameter model locally requires massive GPU arrays (e.g., 4x A100s), driving baseline infrastructure costs to over $4,000/month regardless of usage. 
**HOW**: The `InferenceClient` acts as a lightweight HTTP wrapper matching the OpenAI Messages API format.
**PRODUCTION IMPACT**: Near-zero idle cost. Infinite scalability within rate limits. We avoid maintaining complex CUDA environments.
**INTERVIEW QUESTION**: "Why didn't you deploy a local model for data privacy?"
*Answer*: "Local deployment was rejected because it introduces a massive fixed cost that destroys our unit economics. For data privacy, if necessary, Hugging Face provides Dedicated Endpoints which guarantee compliance while still offloading infrastructure management, but Serverless is perfect for non-PHI processing."

## 2. Model Selection Evaluation

### Candidate A: `mistralai/Mixtral-8x7B-Instruct-v0.1`
- **Context Length**: 32,000 tokens
- **Inference Availability**: High (Serverless)
- **JSON Support**: Requires strict prompt engineering (JSON Mode only).
- **Latency**: Very Fast.
- **Cost**: Extremely low.
- **Weakness**: Struggles with deeply nested hierarchical JSON schemas (e.g., complex recursive medical records).

### Candidate B: `Qwen/Qwen2.5-72B-Instruct`
- **Context Length**: 128,000 tokens
- **Inference Availability**: High (Serverless)
- **JSON Support**: High.
- **Latency**: Fast.
- **Cost**: Low.
- **Strengths**: Outstanding multilingual support and giant context window for 100+ page documents.

### Candidate C: `meta-llama/Meta-Llama-3.1-70B-Instruct` (SELECTED)
- **Context Length**: 128,000 tokens
- **Inference Availability**: Very High (Serverless and Dedicated)
- **JSON Support**: Native strict grammar support via Hugging Face Text Generation Inference (TGI).
- **Latency**: Fast.
- **Cost**: Low (~$0.80 / 1M tokens).
- **Strengths**: Llama 3.1 70B is widely considered the open-source equivalent to GPT-4 class models for data extraction and reasoning. It follows system prompts aggressively and handles JSON syntax flawlessly.

## 3. Implementation Decision
**WHAT**: `meta-llama/Meta-Llama-3.1-70B-Instruct` will be our default open-source fallback.
**HOW**: Configured via `HF_MODEL` or hardcoded fallback.
**TRADEOFF**: 70B models have higher time-to-first-token (TTFT) latency compared to 8B models, but we cannot sacrifice accuracy in structured extraction.

## 4. Structured Output Approach
**WHAT**: Use Hugging Face's `response_format` with JSON Schema constraint.
**WHY**: Modern Hugging Face Inference API uses TGI (Text Generation Inference) which supports `type: "json_schema"`. This uses constrained decoding to guarantee valid JSON, functionally matching OpenAI's strict structured output.
**HOW**: We pass `schema.model_json_schema()` directly to the `InferenceClient` and validate via Pydantic upon return.
