#!/usr/bin/env python3
"""
Test script to verify Unstructured API feature toggles
"""
import os

# Test the is_unstructured_enabled function
def is_unstructured_enabled(file_ext: str) -> bool:
    """Check if Unstructured API should be used for this file type"""
    env_var = f"UNSTRUCTURED_ENABLED_{file_ext.upper().lstrip('.')}"
    value = os.getenv(env_var, "true").lower()
    return value in ("true", "1", "yes")

# Test cases
test_cases = [
    (".pdf", True),
    (".docx", True),
    (".doc", True),
    (".ppt", True),
    (".pptx", True),
    (".xml", True),
    (".epub", True),
    (".msg", True),
    (".eml", True),
    (".md", True),
]

print("Testing Unstructured API feature toggles:\n")
print(f"{'File Extension':<15} {'Expected':<10} {'Actual':<10} {'Status':<10}")
print("-" * 50)

all_passed = True
for ext, expected in test_cases:
    actual = is_unstructured_enabled(ext)
    status = "✓ PASS" if actual == expected else "✗ FAIL"
    if actual != expected:
        all_passed = False
    print(f"{ext:<15} {str(expected):<10} {str(actual):<10} {status:<10}")

print("\n" + "=" * 50)
if all_passed:
    print("✓ All tests passed!")
else:
    print("✗ Some tests failed!")

# Test with disabled feature
print("\n\nTesting with UNSTRUCTURED_ENABLED_DOCX=false:")
os.environ["UNSTRUCTURED_ENABLED_DOCX"] = "false"
result = is_unstructured_enabled(".docx")
print(f"is_unstructured_enabled('.docx') = {result}")
print(f"Expected: False, Got: {result} - {'✓ PASS' if not result else '✗ FAIL'}")
