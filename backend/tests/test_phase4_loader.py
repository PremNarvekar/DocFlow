"""
PHASE 4 — PDF LOADER TESTING
Tests loader.py with various PDF scenarios.
Creates test PDFs programmatically using PyMuPDF.
"""
import sys
import os
import time
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import fitz  # PyMuPDF
from pydantic import ValidationError

from pipeline.loader import load_and_extract, LoadedDocument, PageContent

PASS = 0
FAIL = 0
RESULTS = []


def record(test_name, expected, actual, passed, critique=""):
    global PASS, FAIL
    status = "PASS" if passed else "FAIL"
    if passed:
        PASS += 1
    else:
        FAIL += 1
    RESULTS.append({
        "test": test_name,
        "expected": expected,
        "actual": actual,
        "status": status,
        "critique": critique,
    })
    icon = "✓" if passed else "✗"
    print(f"  {icon} {test_name}: {status}")
    if not passed:
        print(f"    Expected: {expected}")
        print(f"    Actual: {actual}")
    if critique:
        print(f"    CRITIQUE: {critique}")


def create_test_pdf(path, pages_text):
    """Create a test PDF with specified text on each page."""
    doc = fitz.open()
    for text in pages_text:
        page = doc.new_page()
        if text:
            page.insert_text((72, 72), text, fontsize=12)
    doc.save(str(path))
    doc.close()


# Create temp directory for test files
test_dir = Path(__file__).resolve().parent / "test_pdfs"
test_dir.mkdir(exist_ok=True)

print("=" * 60)
print("PHASE 4: PDF LOADER TESTS")
print("=" * 60)

# ============================================================
# Test 1: Normal text PDF (1 page)
# ============================================================
print("\n--- Test: Normal single-page PDF ---")
pdf_path = test_dir / "normal_single.pdf"
create_test_pdf(pdf_path, ["This is a normal test document with some text content."])

try:
    result = load_and_extract(str(pdf_path))
    passed = (
        isinstance(result, LoadedDocument)
        and result.page_count == 1
        and len(result.pages) == 1
        and result.pages[0].page_num == 1
        and "normal test document" in result.pages[0].text
        and result.file_name == "normal_single.pdf"
    )
    record(
        "Loader: Normal single-page PDF",
        "1 page with text",
        f"Pages: {result.page_count}, Text contains 'normal test document': {'normal test document' in result.pages[0].text}",
        passed,
    )
except Exception as e:
    record("Loader: Normal single-page PDF", "1 page with text", f"Error: {e}", False)

# ============================================================
# Test 2: Multi-page PDF
# ============================================================
print("\n--- Test: Multi-page PDF ---")
pdf_path = test_dir / "multi_page.pdf"
create_test_pdf(pdf_path, [
    "Page 1: Introduction to the document",
    "Page 2: Main content of the document",
    "Page 3: Conclusion and summary",
])

try:
    result = load_and_extract(str(pdf_path))
    passed = (
        result.page_count == 3
        and len(result.pages) == 3
        and result.pages[0].page_num == 1
        and result.pages[1].page_num == 2
        and result.pages[2].page_num == 3
        and "Page 1" in result.pages[0].text
        and "Page 2" in result.pages[1].text
        and "Page 3" in result.pages[2].text
    )
    record(
        "Loader: Multi-page PDF",
        "3 pages with correct numbering and text",
        f"Pages: {result.page_count}, Page numbers: {[p.page_num for p in result.pages]}",
        passed,
    )
except Exception as e:
    record("Loader: Multi-page PDF", "3 pages", f"Error: {e}", False)

# ============================================================
# Test 3: Invalid file path
# ============================================================
print("\n--- Test: Invalid file path ---")
try:
    result = load_and_extract("nonexistent_file.pdf")
    record("Loader: Invalid file path", "FileNotFoundError", "No error raised", False)
except FileNotFoundError as e:
    record("Loader: Invalid file path", "FileNotFoundError", f"FileNotFoundError: {e}", True)
except Exception as e:
    record("Loader: Invalid file path", "FileNotFoundError", f"{type(e).__name__}: {e}", False)

# ============================================================
# Test 4: Non-PDF file
# ============================================================
print("\n--- Test: Non-PDF file ---")
txt_path = test_dir / "not_a_pdf.txt"
txt_path.write_text("This is a text file, not a PDF.")

try:
    result = load_and_extract(str(txt_path))
    record("Loader: Non-PDF file", "ValueError", "No error raised", False,
           critique="Non-PDF files should be rejected.")
except ValueError as e:
    record("Loader: Non-PDF file", "ValueError", f"ValueError: {e}", True)
except Exception as e:
    record("Loader: Non-PDF file", "ValueError", f"{type(e).__name__}: {e}", False)

# ============================================================
# Test 5: PDF with empty pages
# ============================================================
print("\n--- Test: PDF with empty pages ---")
pdf_path = test_dir / "empty_pages.pdf"
create_test_pdf(pdf_path, ["", "Some text on page 2", ""])

try:
    result = load_and_extract(str(pdf_path))
    passed = (
        result.page_count == 3
        and len(result.pages) == 3
        and result.pages[0].text == ""
        and "Some text on page 2" in result.pages[1].text
        and result.pages[2].text == ""
    )
    record(
        "Loader: PDF with empty pages",
        "3 pages, pages 1 and 3 empty",
        f"Pages: {result.page_count}, Empty pages: {[p.page_num for p in result.pages if not p.text]}",
        passed,
        critique="Empty pages are included in the result. This is acceptable for provenance tracking "
                 "but may cause issues if the empty text is sent to the LLM for classification."
    )
except Exception as e:
    record("Loader: PDF with empty pages", "3 pages", f"Error: {e}", False)

# ============================================================
# Test 6: Empty PDF (0 pages) — PyMuPDF doesn't easily create 0-page PDFs
# We'll test with a valid PDF that has no text
# ============================================================
print("\n--- Test: PDF with all-empty content ---")
pdf_path = test_dir / "all_empty.pdf"
create_test_pdf(pdf_path, [""])

try:
    result = load_and_extract(str(pdf_path))
    all_text = "".join(p.text for p in result.pages)
    record(
        "Loader: All-empty PDF",
        "Loads but text is empty",
        f"Pages: {result.page_count}, Total text length: {len(all_text)}",
        result.page_count >= 1 and len(all_text.strip()) == 0,
        critique="The loader loads a PDF with no extractable text. This is a valid PDF (1 page) "
                 "but has no content. The classifier will receive empty text and should return UNKNOWN. "
                 "However, the loader itself does not flag this condition."
    )
except ValueError as e:
    if "no pages" in str(e).lower():
        record("Loader: All-empty PDF", "Loads or raises ValueError", f"ValueError: {e}", True)
    else:
        record("Loader: All-empty PDF", "Loads or raises ValueError", f"ValueError: {e}", False)
except Exception as e:
    record("Loader: All-empty PDF", "Loads or raises ValueError", f"Error: {e}", False)

# ============================================================
# Test 7: Corrupted / invalid file with .pdf extension
# ============================================================
print("\n--- Test: Corrupted file with .pdf extension ---")
corrupted_path = test_dir / "corrupted.pdf"
corrupted_path.write_bytes(b"This is not a valid PDF file content at all")

try:
    result = load_and_extract(str(corrupted_path))
    record("Loader: Corrupted .pdf file", "Error raised", "No error raised", False,
           critique="CRITICAL: A corrupted file with .pdf extension was accepted without error.")
except Exception as e:
    record("Loader: Corrupted .pdf file", "Error raised",
           f"{type(e).__name__}: {str(e)[:100]}", True,
           critique="Good: corrupted PDF raises an error. But the error type may not be descriptive enough for users.")

# ============================================================
# Test 8: Large PDF (50 pages)
# ============================================================
print("\n--- Test: Large PDF (50 pages) ---")
pdf_path = test_dir / "large_50_pages.pdf"
large_pages = [f"Page {i+1}: {'Lorem ipsum dolor sit amet. ' * 50}" for i in range(50)]

start_time = time.time()
create_test_pdf(pdf_path, large_pages)
create_time = time.time() - start_time

start_time = time.time()
try:
    result = load_and_extract(str(pdf_path))
    extract_time = time.time() - start_time
    total_chars = sum(len(p.text) for p in result.pages)
    record(
        "Loader: Large PDF (50 pages)",
        "50 pages extracted",
        f"Pages: {result.page_count}, Total chars: {total_chars}, Time: {extract_time:.3f}s",
        result.page_count == 50 and len(result.pages) == 50,
        critique=f"50-page PDF extracted in {extract_time:.3f}s ({total_chars} chars). "
                 f"At this rate, a 755-page PDF would take ~{extract_time/50*755:.1f}s for extraction alone."
    )
except Exception as e:
    record("Loader: Large PDF (50 pages)", "50 pages", f"Error: {e}", False)

# ============================================================
# Test 9: Resource cleanup (file not locked after extraction)
# ============================================================
print("\n--- Test: Resource cleanup ---")
pdf_path = test_dir / "cleanup_test.pdf"
create_test_pdf(pdf_path, ["Test cleanup"])

try:
    result = load_and_extract(str(pdf_path))
    # Try to delete the file — if the document wasn't closed, this will fail on Windows
    try:
        pdf_path.unlink()
        record("Loader: Resource cleanup", "File can be deleted after extraction", "File deleted successfully", True,
               critique="Good: PyMuPDF document is properly closed in the finally block.")
    except PermissionError:
        record("Loader: Resource cleanup", "File can be deleted", "PermissionError — file still locked", False,
               critique="CRITICAL: The PDF file is still locked after extraction. The document.close() is not working.")
except Exception as e:
    record("Loader: Resource cleanup", "Extraction succeeds", f"Error: {e}", False)

# ============================================================
# Test 10: Scanned PDF simulation (image-only page)
# ============================================================
print("\n--- Test: Scanned PDF simulation ---")
pdf_path = test_dir / "scanned_simulation.pdf"
# Create a PDF with only a drawn rectangle (no text)
doc = fitz.open()
page = doc.new_page()
page.draw_rect(fitz.Rect(100, 100, 400, 400), color=(0, 0, 0), width=2)
doc.save(str(pdf_path))
doc.close()

try:
    result = load_and_extract(str(pdf_path))
    has_text = any(p.text.strip() for p in result.pages)
    record(
        "Loader: Scanned PDF (no extractable text)",
        "Loads but with empty text",
        f"Pages: {result.page_count}, Has extractable text: {has_text}",
        not has_text,
        critique="KNOWN LIMITATION: Scanned/image-only PDFs return empty text. "
                 "The system currently has no OCR fallback. This means scanned documents "
                 "will be classified as UNKNOWN and no data will be extracted."
    )
except Exception as e:
    record("Loader: Scanned PDF", "Loads with empty text", f"Error: {e}", False)

# ============================================================
# Test 11: Page number consistency
# ============================================================
print("\n--- Test: Page numbering is 1-indexed ---")
pdf_path = test_dir / "page_numbering.pdf"
create_test_pdf(pdf_path, ["A", "B", "C", "D", "E"])

try:
    result = load_and_extract(str(pdf_path))
    page_nums = [p.page_num for p in result.pages]
    expected_nums = [1, 2, 3, 4, 5]
    record(
        "Loader: Page numbers are 1-indexed",
        str(expected_nums),
        str(page_nums),
        page_nums == expected_nums,
    )
except Exception as e:
    record("Loader: Page numbering", "1-indexed", f"Error: {e}", False)

# ============================================================
# Test 12: file_path stored as string
# ============================================================
print("\n--- Test: file_path stored correctly ---")
pdf_path = test_dir / "path_test.pdf"
create_test_pdf(pdf_path, ["Test"])

try:
    result = load_and_extract(str(pdf_path))
    record(
        "Loader: file_path stored as string",
        "String path stored",
        f"file_path type: {type(result.file_path).__name__}, value: {result.file_path}",
        isinstance(result.file_path, str) and str(pdf_path) == result.file_path,
    )
except Exception as e:
    record("Loader: file_path", "String path", f"Error: {e}", False)


# ============================================================
# MEMORY ANALYSIS
# ============================================================
print("\n--- Memory Analysis ---")
print("  NOTE: The current loader stores ALL page text in memory as a list of PageContent objects.")
print("  For a 755-page document with ~1KB per page, this is ~755KB — manageable.")
print("  For a 755-page document with ~10KB per page (dense text), this is ~7.5MB — still manageable.")
print("  The REAL concern is when this entire text is concatenated and sent to the LLM.")
print("  Gemini's context window is large but has token limits, and sending 755 pages of text")
print("  would be extremely expensive and potentially exceed the token limit.")


# ============================================================
# Cleanup
# ============================================================
print("\n--- Cleanup ---")
import shutil
try:
    shutil.rmtree(test_dir)
    print("  Test PDFs cleaned up.")
except Exception as e:
    print(f"  Cleanup warning: {e}")


# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 60)
print("LOADER TEST SUMMARY")
print("=" * 60)
print(f"Total: {PASS + FAIL}")
print(f"PASS:  {PASS}")
print(f"FAIL:  {FAIL}")

print()
print("WEAKNESSES FOUND:")
weaknesses = [r for r in RESULTS if r.get("critique") and ("WEAKNESS" in r["critique"] or "CRITICAL" in r["critique"] or "LIMITATION" in r["critique"])]
for i, w in enumerate(weaknesses, 1):
    print(f"  {i}. [{w['test']}] {w['critique']}")
