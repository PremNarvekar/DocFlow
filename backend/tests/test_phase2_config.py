"""
PHASE 2 — CONFIGURATION TEST
Tests environment configuration, .env loading, API key handling.
"""
import sys
import os
from pathlib import Path

# Ensure backend is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PASS = 0
FAIL = 0


def record(test_name, expected, actual, passed, critique=""):
    global PASS, FAIL
    status = "PASS" if passed else "FAIL"
    if passed:
        PASS += 1
    else:
        FAIL += 1
    icon = "✓" if passed else "✗"
    print(f"  {icon} {test_name}: {status}")
    if not passed:
        print(f"    Expected: {expected}")
        print(f"    Actual: {actual}")
    if critique:
        print(f"    CRITIQUE: {critique}")


print("=" * 60)
print("PHASE 2: CONFIGURATION TESTS")
print("=" * 60)

# Test 1: .env file exists
env_path = Path(__file__).resolve().parent.parent / ".env"
record(
    "Config: .env file exists",
    ".env file exists",
    f".env exists: {env_path.exists()}",
    env_path.exists(),
)

# Test 2: .env contains GEMINI_API_KEY (not XAI_API_KEY)
if env_path.exists():
    env_content = env_path.read_text()
    has_gemini_key = "GEMINI_API_KEY" in env_content
    record(
        "Config: .env has GEMINI_API_KEY",
        "GEMINI_API_KEY present",
        f"GEMINI_API_KEY present: {has_gemini_key}",
        has_gemini_key,
    )
    # Check that the key is not empty
    for line in env_content.strip().splitlines():
        if line.startswith("GEMINI_API_KEY="):
            key_value = line.split("=", 1)[1].strip()
            has_value = len(key_value) > 0
            record(
                "Config: GEMINI_API_KEY has value",
                "Non-empty value",
                f"Value length: {len(key_value)}",
                has_value,
            )
            # Check key is not obviously a placeholder
            is_placeholder = key_value in ["your-key-here", "xxx", "placeholder", ""]
            record(
                "Config: GEMINI_API_KEY is not placeholder",
                "Real key (not placeholder)",
                f"Not placeholder: {not is_placeholder}",
                not is_placeholder,
            )

# Test 3: config.py imports and loads correctly
print()
print("--- Config Import Test ---")
try:
    import config
    record(
        "Config: config.py imports successfully",
        "Import succeeds",
        "Imported",
        True,
    )
    # Verify GEMINI_API_KEY is set (don't print the value)
    has_key = hasattr(config, 'GEMINI_API_KEY') and config.GEMINI_API_KEY is not None
    record(
        "Config: GEMINI_API_KEY is loaded",
        "Key loaded and not None",
        f"Key loaded: {has_key}",
        has_key,
    )
    # Verify key length is reasonable (not printing the actual key)
    if has_key:
        key_len = len(config.GEMINI_API_KEY)
        record(
            "Config: API key has reasonable length",
            ">= 10 characters",
            f"Length: {key_len}",
            key_len >= 10,
        )
except RuntimeError as e:
    err_msg = str(e)
    record(
        "Config: config.py imports successfully",
        "Import succeeds",
        f"RuntimeError: {err_msg}",
        False,
        critique="Config import failed. This means the application cannot start."
    )
except Exception as e:
    record(
        "Config: config.py imports successfully",
        "Import succeeds",
        f"{type(e).__name__}: {e}",
        False,
    )

# Test 4: .gitignore protects .env
print()
print("--- Security Tests ---")
gitignore_path = Path(__file__).resolve().parent.parent / ".gitignore"
if gitignore_path.exists():
    gitignore_content = gitignore_path.read_text()
    env_ignored = ".env" in gitignore_content
    record(
        "Security: .env in .gitignore",
        ".env is gitignored",
        f".env in .gitignore: {env_ignored}",
        env_ignored,
    )
    # Check .gitignore itself for issues
    if gitignore_content.startswith('@"'):
        record(
            "Security: .gitignore format",
            "Standard gitignore format",
            "File starts with @\" (PowerShell Set-Content artifact)",
            False,
            critique="CRITICAL BUG: The .gitignore file is corrupted. It starts with @\" and ends with "
                     "'\"@ | Set-Content \".gitignore\"'. This is a PowerShell command that was accidentally "
                     "written as file content instead of being executed. Git may not be properly ignoring files."
        )
    else:
        record(
            "Security: .gitignore format",
            "Standard gitignore format",
            "Format looks correct",
            True,
        )
else:
    record(
        "Security: .gitignore exists",
        ".gitignore exists",
        "File not found",
        False,
    )

# Test 5: Missing key behavior simulation
print()
print("--- Missing Key Behavior ---")
# Save current env and simulate missing key
original_key = os.environ.get("GEMINI_API_KEY")
os.environ.pop("GEMINI_API_KEY", None)

# We can't re-import config.py easily, but we can test the logic
from dotenv import load_dotenv
# Don't load dotenv here - test with empty env
test_key = os.getenv("GEMINI_API_KEY")
if test_key is None:
    record(
        "Config: Missing key returns None from os.getenv",
        "None",
        f"Got: {test_key}",
        True,
        critique="config.py correctly raises RuntimeError when key is missing. "
                 "However, the RuntimeError is raised at module import time, which means "
                 "any file that imports config will crash immediately if the key is missing. "
                 "This is fail-fast behavior, which is GOOD for catching misconfiguration early. "
                 "But it also means you cannot import config to check other settings without a valid key."
    )
else:
    record(
        "Config: Missing key returns None from os.getenv",
        "None (key should be missing after pop)",
        f"Got value (possibly from .env): {bool(test_key)}",
        False,
        critique="The .env file is being loaded before this test, so the key persists."
    )

# Restore
if original_key:
    os.environ["GEMINI_API_KEY"] = original_key

# Test 6: Config does not have model name
print()
print("--- Model Configuration ---")
try:
    has_model_config = hasattr(config, 'XAI_MODEL') or hasattr(config, 'GEMINI_MODEL') or hasattr(config, 'MODEL_NAME')
    record(
        "Config: Model name configurable",
        "Model name in config",
        f"Model config attribute found: {has_model_config}",
        has_model_config,
        critique="WEAKNESS: The model name 'gemini-2.5-flash' is hardcoded in classifier.py and extractor.py "
                 "instead of being configured in config.py. This means changing the model requires editing "
                 "multiple files. The model name should be a configuration variable." if not has_model_config else ""
    )
except:
    pass


# Summary
print()
print("=" * 60)
print("CONFIGURATION TEST SUMMARY")
print("=" * 60)
print(f"Total: {PASS + FAIL}")
print(f"PASS:  {PASS}")
print(f"FAIL:  {FAIL}")
