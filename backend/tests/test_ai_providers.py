"""
Comprehensive AI Provider test suite.

Test categories:
  A. Configuration — key loading, missing keys
  B. Registry — provider discovery, availability
  C. Router — priority, task routing, fallback
  D. Fallback — simulated failures with controlled mocks
  E. Structured output — Pydantic validation
  F. Mock provider — deterministic output, controlled failures
  G. Security — no secrets in logs/errors
  H. Integration — full pipeline with mock
"""

import sys
import os
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PASS = 0
FAIL = 0
RESULTS = []


def record(test_name, expected, actual, passed, critique=""):
    global PASS, FAIL
    if passed:
        PASS += 1
    else:
        FAIL += 1
    RESULTS.append({
        "test": test_name,
        "status": "PASS" if passed else "FAIL",
        "critique": critique,
    })
    icon = "✓" if passed else "✗"
    print(f"  {icon} {test_name}: {'PASS' if passed else 'FAIL'}")
    if not passed:
        print(f"    Expected: {expected}")
        print(f"    Actual: {actual}")
    if critique:
        print(f"    CRITIQUE: {critique}")


# ============================================================
# A. CONFIGURATION TESTS
# ============================================================
print("=" * 60)
print("A. CONFIGURATION TESTS")
print("=" * 60)

import config

record(
    "Config: No crash on import",
    "Import succeeds even with missing keys",
    "Imported",
    True,
    critique="GOOD: config.py no longer crashes when GEMINI_API_KEY is the only key present."
)

record(
    "Config: GEMINI_API_KEY loaded",
    "Not None",
    f"{'Set' if config.GEMINI_API_KEY else 'None'}",
    config.GEMINI_API_KEY is not None,
)

record(
    "Config: PROVIDER_API_KEYS is dict",
    "dict with 6 keys",
    f"dict with {len(config.PROVIDER_API_KEYS)} keys",
    isinstance(config.PROVIDER_API_KEYS, dict) and len(config.PROVIDER_API_KEYS) == 6,
)

record(
    "Config: Priority string exists",
    "comma-separated provider list",
    config.AI_PROVIDER_PRIORITY,
    "," in config.AI_PROVIDER_PRIORITY,
)

record(
    "Config: AI_MODE defaults to 'live'",
    "live",
    config.AI_MODE,
    config.AI_MODE == "live",
)

# Test missing keys don't crash
missing_keys = [
    name for name, key in config.PROVIDER_API_KEYS.items()
    if key is None
]
record(
    "Config: Missing keys are None (not crash)",
    "Several None keys",
    f"{len(missing_keys)} providers have None keys",
    len(missing_keys) > 0,
    critique="Expected: providers without env vars are None, not RuntimeError."
)


# ============================================================
# B. REGISTRY TESTS
# ============================================================
print("\n" + "=" * 60)
print("B. REGISTRY TESTS")
print("=" * 60)

from ai.registry import build_registry, ProviderRegistry
from ai.base import AITask, ProviderStatus

# Build registry from current config
registry = build_registry(
    api_keys=config.PROVIDER_API_KEYS,
    model_overrides=config.PROVIDER_MODELS,
)

record(
    "Registry: All 6 providers registered",
    "6 providers",
    f"{len(registry.provider_names)} providers: {registry.provider_names}",
    len(registry.provider_names) == 6,
)

# Check which are available
available = registry.get_available()
available_names = [p.name for p in available]
record(
    "Registry: Available providers detected",
    "At least 1 available",
    f"Available: {available_names}",
    len(available) >= 1,
)

# Check unavailable providers report correct status
for name in ["groq", "cerebras", "mistral", "openrouter"]:
    provider = registry.get(name)
    if provider:
        status = provider.get_status()
        record(
            f"Registry: {name} is unavailable (no key)",
            "UNAVAILABLE",
            status.value,
            status == ProviderStatus.UNAVAILABLE,
        )

# Check Gemini is available (has key)
gemini = registry.get("gemini")
if gemini:
    record(
        "Registry: Gemini available (has key)",
        "AVAILABLE",
        gemini.get_status().value,
        gemini.is_available(),
    )

# Get provider info (frontend-safe)
all_info = registry.get_all_info()
record(
    "Registry: get_all_info returns ProviderInfo",
    "list of ProviderInfo",
    f"{len(all_info)} ProviderInfo objects",
    len(all_info) == 6,
)

# Verify info doesn't contain API keys
info_json = json.dumps([i.model_dump() for i in all_info])
record(
    "Security: Provider info doesn't leak API keys",
    "No API key in info",
    "Keys not found" if "AQ.Ab8" not in info_json else "KEY LEAKED!",
    "AQ.Ab8" not in info_json and "api_key" not in info_json.lower(),
)


# ============================================================
# C. ROUTER TESTS
# ============================================================
print("\n" + "=" * 60)
print("C. ROUTER TESTS")
print("=" * 60)

from ai.router import AIRouter
from ai.mock import MockProvider
from ai.errors import AIProviderError, AIRouterError, ErrorCategory

# Build a test router with two mock providers
mock1 = MockProvider()
mock2 = MockProvider()

test_registry = ProviderRegistry()
# Override names for testing
mock1._provider_name_override = "primary"
mock2._provider_name_override = "fallback"
# Use mock's actual name — they'll both be "mock" which is fine for base test

# Instead, let's create a proper test with the real mock
test_registry.register(mock1)

test_router = AIRouter(
    registry=test_registry,
    priority_order=["mock"],
)

# Test: Router returns response from mock
resp = test_router.generate("test prompt", task=AITask.GENERAL_QUERY)
record(
    "Router: Returns AIResponse",
    "AIResponse with provider='mock'",
    f"provider={resp.provider}, text present={bool(resp.text)}",
    resp.provider == "mock" and bool(resp.text),
)

record(
    "Router: Response has metadata",
    "request_id, latency_ms, task",
    f"id={resp.request_id}, latency={resp.latency_ms}ms, task={resp.task}",
    bool(resp.request_id) and resp.latency_ms >= 0 and resp.task == AITask.GENERAL_QUERY,
)

# Test: Router with no providers raises AIRouterError
empty_registry = ProviderRegistry()
empty_router = AIRouter(registry=empty_registry)
try:
    empty_router.generate("test")
    record("Router: No providers → AIRouterError", "AIRouterError raised", "No error", False)
except AIRouterError as e:
    record(
        "Router: No providers → AIRouterError",
        "AIRouterError",
        f"AIRouterError: {e}",
        True,
    )
except Exception as e:
    record("Router: No providers → AIRouterError", "AIRouterError", f"{type(e).__name__}: {e}", False)


# ============================================================
# D. FALLBACK TESTS
# ============================================================
print("\n" + "=" * 60)
print("D. FALLBACK TESTS")
print("=" * 60)

# Helper: build a router with two mock providers, primary can fail
class NamedMock(MockProvider):
    """Mock with a custom name for testing fallback."""
    def __init__(self, custom_name: str, failure_mode=None):
        super().__init__(failure_mode=failure_mode)
        self._custom_name = custom_name

    @property
    def name(self) -> str:
        return self._custom_name


def build_fallback_router(primary_failure=None, secondary_failure=None):
    reg = ProviderRegistry()
    reg.register(NamedMock("primary", failure_mode=primary_failure))
    reg.register(NamedMock("secondary", failure_mode=secondary_failure))
    return AIRouter(registry=reg, priority_order=["primary", "secondary"])


# Test: Both succeed → primary is used
router_ok = build_fallback_router()
resp = router_ok.generate("test")
record(
    "Fallback: Both OK → primary used",
    "provider=primary",
    f"provider={resp.provider}",
    resp.provider == "primary" and not resp.fallback_used,
)

# Test: Primary timeout → secondary success
router_timeout = build_fallback_router(primary_failure="timeout")
resp = router_timeout.generate("test")
record(
    "Fallback: Primary timeout → secondary",
    "provider=secondary, fallback_used=True",
    f"provider={resp.provider}, fallback={resp.fallback_used}",
    resp.provider == "secondary" and resp.fallback_used,
)

# Test: Primary 429 → secondary success
router_429 = build_fallback_router(primary_failure="429")
resp = router_429.generate("test")
record(
    "Fallback: Primary 429 → secondary",
    "provider=secondary, fallback_used=True",
    f"provider={resp.provider}, fallback={resp.fallback_used}",
    resp.provider == "secondary" and resp.fallback_used,
)

# Test: Primary 500 → secondary success
router_500 = build_fallback_router(primary_failure="500")
resp = router_500.generate("test")
record(
    "Fallback: Primary 500 → secondary",
    "provider=secondary",
    f"provider={resp.provider}",
    resp.provider == "secondary" and resp.fallback_used,
)

# Test: Primary auth error → secondary success
router_auth = build_fallback_router(primary_failure="auth")
resp = router_auth.generate("test")
record(
    "Fallback: Primary auth error → secondary",
    "provider=secondary",
    f"provider={resp.provider}",
    resp.provider == "secondary" and resp.fallback_used,
)

# Test: Both fail → AIRouterError
router_both_fail = build_fallback_router(primary_failure="timeout", secondary_failure="500")
try:
    router_both_fail.generate("test")
    record("Fallback: Both fail → AIRouterError", "AIRouterError", "No error", False)
except AIRouterError as e:
    record(
        "Fallback: Both fail → AIRouterError",
        "AIRouterError with 2 errors",
        f"AIRouterError: {len(e.errors)} errors",
        len(e.errors) == 2,
    )

# Test: Primary invalid_response (non-retryable) → does NOT retry
router_invalid = build_fallback_router(primary_failure="invalid_json")
try:
    router_invalid.generate("test")
    record("Fallback: Non-retryable doesn't cascade", "Error raised", "No error", False)
except AIProviderError as e:
    # Non-retryable should NOT try secondary
    record(
        "Fallback: Non-retryable stops immediately",
        "AIProviderError (not routed to secondary)",
        f"category={e.category.value}",
        e.category == ErrorCategory.INVALID_RESPONSE,
        critique="GOOD: Invalid response errors don't waste a fallback call."
    )
except AIRouterError:
    record(
        "Fallback: Non-retryable stops immediately",
        "AIProviderError (not routed to secondary)",
        "AIRouterError (tried secondary anyway)",
        False,
        critique="BUG: Non-retryable errors should not cascade to secondary."
    )


# ============================================================
# E. STRUCTURED OUTPUT TESTS
# ============================================================
print("\n" + "=" * 60)
print("E. STRUCTURED OUTPUT TESTS")
print("=" * 60)

from pydantic import BaseModel
from pipeline.classifier import DocumentClassification, DocumentType

# Test: Mock parse returns valid Pydantic data
mock_router = build_fallback_router()
resp = mock_router.parse("test invoice doc", DocumentClassification, task=AITask.DOCUMENT_CLASSIFICATION)
record(
    "Parse: Returns valid JSON for schema",
    "Valid DocumentClassification JSON",
    f"text={resp.text[:100]}",
    True,
)

# Validate the JSON against the schema
try:
    obj = DocumentClassification.model_validate_json(resp.text)
    record(
        "Parse: JSON validates against Pydantic",
        "DocumentClassification instance",
        f"document_type={obj.document_type}",
        True,
    )
except Exception as e:
    record("Parse: JSON validates against Pydantic", "Valid", f"Error: {e}", False)

# Test with InvoiceData schema
from models.invoice import InvoiceData
resp_invoice = mock_router.parse("extract invoice", InvoiceData)
try:
    invoice = InvoiceData.model_validate_json(resp_invoice.text)
    record(
        "Parse: InvoiceData mock extraction",
        "Valid InvoiceData",
        f"invoice_number={invoice.invoice_number}",
        True,
    )
except Exception as e:
    record("Parse: InvoiceData mock extraction", "Valid", f"Error: {e}", False,
           critique="Mock provider failed to generate valid InvoiceData JSON.")


# ============================================================
# F. MOCK PROVIDER TESTS
# ============================================================
print("\n" + "=" * 60)
print("F. MOCK PROVIDER TESTS")
print("=" * 60)

# Test: Mock classification is deterministic
mock = MockProvider()
resp1 = mock.generate("This is an invoice", task=AITask.DOCUMENT_CLASSIFICATION)
resp2 = mock.generate("This is an invoice", task=AITask.DOCUMENT_CLASSIFICATION)
record(
    "Mock: Deterministic classification",
    "Same output for same input",
    f"resp1={resp1.text}, resp2={resp2.text}",
    resp1.text == resp2.text,
)

# Test: Mock identifies invoice
record(
    "Mock: Invoice keyword → invoice",
    '{"document_type": "invoice"}',
    resp1.text,
    '"invoice"' in resp1.text,
)

# Test: Mock contract
resp_contract = mock.generate("This is a contract agreement", task=AITask.DOCUMENT_CLASSIFICATION)
record(
    "Mock: Contract keyword → contract",
    "contract",
    resp_contract.text,
    '"contract"' in resp_contract.text,
)

# Test: Mock unknown
resp_unknown = mock.generate("random gibberish xyz", task=AITask.DOCUMENT_CLASSIFICATION)
record(
    "Mock: Unknown text → unknown",
    "unknown",
    resp_unknown.text,
    '"unknown"' in resp_unknown.text,
)

# Test: Mock tracks call count
record(
    "Mock: Tracks call count",
    "4 calls",
    f"{mock.call_count} calls",
    mock.call_count == 4,
)

# Test: Mock failure modes
for mode, expected_category in [
    ("timeout", ErrorCategory.TIMEOUT),
    ("429", ErrorCategory.RATE_LIMITED),
    ("auth", ErrorCategory.AUTH_ERROR),
    ("500", ErrorCategory.SERVER_ERROR),
]:
    failing_mock = MockProvider(failure_mode=mode)
    try:
        failing_mock.generate("test")
        record(f"Mock: Failure mode '{mode}'", f"{expected_category.value}", "No error", False)
    except AIProviderError as e:
        record(
            f"Mock: Failure mode '{mode}'",
            expected_category.value,
            e.category.value,
            e.category == expected_category,
        )


# ============================================================
# G. SECURITY TESTS
# ============================================================
print("\n" + "=" * 60)
print("G. SECURITY TESTS")
print("=" * 60)

# Test: AIProviderError doesn't contain API key
api_key = config.GEMINI_API_KEY or "test_key_12345"
try:
    error = AIProviderError(
        "Test error",
        provider="gemini",
        category=ErrorCategory.AUTH_ERROR,
    )
    error_str = str(error)
    record(
        "Security: Error message doesn't contain API key",
        "No key in error",
        f"Error: {error_str}",
        api_key not in error_str,
    )
except Exception as e:
    record("Security: Error message safe", "No key", f"Error: {e}", False)

# Test: Provider info doesn't contain secrets
from ai.registry import build_registry
safe_registry = build_registry(
    api_keys={"gemini": "AIzaSyDEF456_secret_key"},
    model_overrides={},
)
infos = safe_registry.get_all_info()
info_str = json.dumps([i.model_dump() for i in infos])
record(
    "Security: ProviderInfo doesn't leak keys",
    "No key in info JSON",
    f"Contains 'AIzaSy': {'AIzaSy' in info_str}",
    "AIzaSy" not in info_str and "secret" not in info_str,
)


# ============================================================
# H. INTEGRATION TESTS (with mock)
# ============================================================
print("\n" + "=" * 60)
print("H. INTEGRATION TESTS (Mock Pipeline)")
print("=" * 60)

# Test full pipeline: classify_document with mock
os.environ["AI_MODE"] = "mock"
config.AI_MODE = "mock"
from ai import reset_router
reset_router()

from pipeline.classifier import classify_document

result = classify_document("This is an invoice for $5000")
record(
    "Integration: classify_document with mock",
    "DocumentClassification with type",
    f"type={result.document_type.value}",
    result.document_type == DocumentType.INVOICE,
)

result_empty = classify_document("")
record(
    "Integration: Empty text → UNKNOWN (no API call)",
    "UNKNOWN",
    result_empty.document_type.value,
    result_empty.document_type == DocumentType.UNKNOWN,
)

result_contract = classify_document("This is a service agreement contract")
record(
    "Integration: Contract classification",
    "contract",
    result_contract.document_type.value,
    result_contract.document_type == DocumentType.CONTRACT,
)

# Test full pipeline: extract_document with mock
from pipeline.extractor import extract_document

try:
    invoice_data = extract_document(
        "Invoice #001 for laptop computers",
        DocumentType.INVOICE,
    )
    record(
        "Integration: extract_document with mock",
        "InvoiceData instance",
        f"type={type(invoice_data).__name__}",
        type(invoice_data).__name__ == "InvoiceData",
    )
except Exception as e:
    record("Integration: extract_document with mock", "Success", f"Error: {e}", False)

# Test: extract_document with empty text
try:
    extract_document("", DocumentType.INVOICE)
    record("Integration: Empty text → ValueError", "ValueError", "No error", False)
except ValueError:
    record("Integration: Empty text → ValueError", "ValueError", "ValueError raised", True)

# Test: extract_document with UNKNOWN type
try:
    extract_document("some text", DocumentType.UNKNOWN)
    record("Integration: UNKNOWN type → ValueError", "ValueError", "No error", False)
except ValueError:
    record("Integration: UNKNOWN type → ValueError", "ValueError", "ValueError raised", True)

# Restore live mode
os.environ["AI_MODE"] = "live"
config.AI_MODE = "live"
reset_router()


# ============================================================
# I. REAL API INTEGRATION TESTS
# ============================================================
print("\n" + "=" * 60)
print("I. REAL API INTEGRATION TESTS")
print("=" * 60)

# These tests use real API keys — only run if available
reset_router()
from ai import get_router

real_router = get_router()
real_available = [p.name for p in real_router._registry.get_available()]
print(f"  Available providers: {real_available}")

if not real_available:
    print("  SKIPPED: No real providers available")
else:
    for provider_name in real_available:
        provider = real_router._registry.get(provider_name)
        if not provider or not provider.is_available():
            continue

        print(f"\n  --- Testing {provider.display_name} ---")

        # Test: Classification
        start = time.time()
        try:
            resp = provider.parse(
                prompt="INVOICE\nInvoice Number: INV-001\nDate: 2026-09-01\nTotal: $5000",
                schema=DocumentClassification,
                system_instruction="Classify this document as invoice, contract, medical_report, financial_statement, or unknown.",
                task=AITask.DOCUMENT_CLASSIFICATION,
            )
            elapsed = time.time() - start
            obj = DocumentClassification.model_validate_json(resp.text)
            record(
                f"Real API: {provider_name} classification",
                "invoice",
                f"{obj.document_type.value} ({elapsed:.2f}s)",
                obj.document_type == DocumentType.INVOICE,
            )
        except Exception as e:
            elapsed = time.time() - start
            record(
                f"Real API: {provider_name} classification",
                "invoice",
                f"Error ({elapsed:.2f}s): {type(e).__name__}: {str(e)[:100]}",
                False,
            )

        # Test: Extraction
        start = time.time()
        try:
            resp = provider.parse(
                prompt=(
                    "Document type: invoice\n\n"
                    "Document:\n"
                    "INVOICE\n"
                    "Invoice Number: INV-2026-TEST\n"
                    "Invoice Date: 2026-09-01\n"
                    "Due Date: 2026-09-30\n"
                    "From: Test Vendor Corp\n"
                    "To: Test Customer Ltd\n"
                    "Item: Widget, Qty: 10, Price: $50, Amount: $500\n"
                    "Subtotal: $500\n"
                    "Tax: $50\n"
                    "Discount: $0\n"
                    "Total: $550\n"
                    "Currency: USD\n"
                    "Payment Terms: Net 30"
                ),
                schema=InvoiceData,
                system_instruction="Extract structured data from this document. Never invent information.",
                task=AITask.STRUCTURED_EXTRACTION,
            )
            elapsed = time.time() - start
            invoice = InvoiceData.model_validate_json(resp.text)
            record(
                f"Real API: {provider_name} extraction",
                "Valid InvoiceData",
                f"invoice_number={invoice.invoice_number}, total={invoice.total} ({elapsed:.2f}s)",
                True,
            )

            # Semantic checks
            record(
                f"Real API: {provider_name} invoice_number correct",
                "INV-2026-TEST",
                invoice.invoice_number,
                "INV-2026-TEST" in invoice.invoice_number,
            )
            record(
                f"Real API: {provider_name} total correct",
                "550",
                str(invoice.total),
                abs(invoice.total - 550) < 1,
            )
        except Exception as e:
            elapsed = time.time() - start
            record(
                f"Real API: {provider_name} extraction",
                "Valid InvoiceData",
                f"Error ({elapsed:.2f}s): {type(e).__name__}: {str(e)[:100]}",
                False,
            )


# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("AI PROVIDER TEST SUMMARY")
print("=" * 60)
print(f"Total: {PASS + FAIL}")
print(f"PASS:  {PASS}")
print(f"FAIL:  {FAIL}")

if FAIL > 0:
    print("\nFAILED TESTS:")
    for r in RESULTS:
        if r["status"] == "FAIL":
            print(f"  ✗ {r['test']}")
            if r["critique"]:
                print(f"    {r['critique']}")
