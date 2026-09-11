# ADR-003: xAI (Grok) as Secondary Fallback Provider

## Context
DocFlow is a production-oriented AI document intelligence platform that handles sensitive classification, structured extraction, and RAG workloads. Our primary AI provider is Google Gemini via the `google-genai` SDK. However, depending on a single AI provider introduces a single point of failure (SPOF). Global API outages, aggressive rate-limiting, or billing account suspensions at the provider level would bring the entire document pipeline to a halt.

## Problem
We need a tier-1 reasoning model capable of highly reliable structured JSON output that operates on completely independent infrastructure from Google Cloud. 

## Decision
We will use **xAI (Grok)** as our primary secondary fallback provider. 

## Alternatives
1. **Azure OpenAI (GPT-4o)**
2. **Anthropic (Claude 3.5 Sonnet)**
3. **Groq (Llama 3)**

## Tradeoffs
- **Anthropic**: Excellent reasoning, but lacks native JSON Mode in its standard API format compared to OpenAI-compatible endpoints, requiring complex prompt-engineering fallbacks.
- **Azure OpenAI**: Extremely reliable but imposes significant enterprise onboarding friction and complex managed-identity authentication layers compared to a simple Bearer token.
- **Groq**: Unmatched latency, but frequently suffers from aggressive rate-limiting on free/standard tiers, making it unreliable as a robust high-throughput fallback.

## Consequences
- xAI utilizes the OpenAI SDK compatibility layer. By inheriting the `OpenAICompatibleProvider`, we gain connection pooling and retry logic without building a custom HTTP client.
- Because xAI may not natively enforce strict JSON Schema mapping on the backend as flawlessly as Gemini's `response_schema`, our adapter must manually serialize the Pydantic schema into the system prompt and explicitly validate the JSON response post-generation.

## Operational impact
If Google GenAI experiences a catastrophic failure, our Router will detect the `503 Server Error` and immediately reroute the `AITask` to xAI. The pipeline (Celery workers, extractors, storage) remains entirely oblivious to the failure, maintaining 100% uptime for the end user. We must ensure `XAI_API_KEY` is consistently rotated and monitored alongside the Gemini key.

## Interview explanation
"Why did you use Grok as a fallback instead of another instance of Gemini in a different region?"

*Answer:* "Regional failovers protect against specific data center outages, but they do not protect against a systemic Google GenAI API global outage, or an aggressive rate-limit block on our specific GCP billing account. By using xAI, we route our fallback traffic through completely independent hardware, networking, and billing infrastructure, granting true high availability."
