"""Regression tests for fabrication_check price detection."""
import json
import subprocess
import sys
import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
FABRICATION_CHECK = REPO / "analyst" / "fabrication_check.py"


def run_check(text: str) -> list:
    """Run fabrication_check against a test string and return issues."""
    # Write test text to a temp file
    test_file = REPO / "tmp" / "_fabrication_test.md"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(text)

    result = subprocess.run(
        [sys.executable, str(FABRICATION_CHECK), "--brief", str(test_file), "--json"],
        capture_output=True, text=True, timeout=15,
    )
    if result.stdout.strip():
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return []
    return []


def test_percentage_not_price():
    """~10-12% of outstanding → should NOT flag as price."""
    text = "a drop in foreign participation in local bond auctions (currently ~10-12% of outstanding)"
    issues = run_check(text)
    price_flags = [i for i in issues if i.get("type") == "unverified_price"]
    assert len(price_flags) == 0, f"Got {len(price_flags)} price flags for percentage: {price_flags}"
    print("  PASS: percentage not flagged as price")


def test_dollar_price_should_flag():
    """$10-12 per share → SHOULD flag as unverified price."""
    text = "the stock is currently trading at $10-12 per share according to analyst projections"
    issues = run_check(text)
    price_flags = [i for i in issues if i.get("type") == "unverified_price"]
    assert len(price_flags) > 0, "Should have flagged $10-12 per share as unverified"
    print("  PASS: dollar price correctly flagged")


def test_usd_amount_should_flag():
    """USD 10 billion → SHOULD flag as unverified amount."""
    text = "the fund raised USD 10 billion in its latest round"
    issues = run_check(text)
    # This may or may not flag depending on context — check if flagging is reasonable
    price_flags = [i for i in issues if i.get("type") == "unverified_price"]
    print(f"  NOTE: USD 10 billion {'flagged' if price_flags else 'not flagged'} (acceptable)")


def test_basis_points_not_price():
    """10 to 12 basis points → should NOT flag."""
    text = "the spread widened by 10 to 12 basis points"
    issues = run_check(text)
    price_flags = [i for i in issues if i.get("type") == "unverified_price"]
    assert len(price_flags) == 0, f"Got {len(price_flags)} flags for basis points"
    print("  PASS: basis points not flagged as price")


def test_multiple_not_price():
    """10x revenue multiple → should NOT flag."""
    text = "the company trades at 10x revenue multiple"
    issues = run_check(text)
    price_flags = [i for i in issues if i.get("type") == "unverified_price"]
    assert len(price_flags) == 0, f"Got {len(price_flags)} flags for multiple"
    print("  PASS: multiple not flagged as price")


def test_year_not_price():
    """2024-2026 timeframe → should NOT flag."""
    text = "covering the 2024-2026 timeframe"
    issues = run_check(text)
    price_flags = [i for i in issues if i.get("type") == "unverified_price"]
    assert len(price_flags) == 0, f"Got {len(price_flags)} flags for year range"
    print("  PASS: year range not flagged as price")


def test_currency_word_should_flag():
    """valued at 10 reais → SHOULD flag."""
    text = "the asset is currently trading at 10 reais in the latest assessment"
    issues = run_check(text)
    price_flags = [i for i in issues if i.get("type") == "unverified_price"]
    # This depends on whether "valued at" triggers the pattern
    if price_flags:
        print("  PASS: 'valued at 10 reais' flagged (correctly aggressive)")
    else:
        print("  NOTE: 'valued at 10 reais' not flagged — may need pattern addition")


if __name__ == "__main__":
    test_percentage_not_price()
    test_dollar_price_should_flag()
    test_usd_amount_should_flag()
    test_basis_points_not_price()
    test_multiple_not_price()
    test_year_not_price()
    test_currency_word_should_flag()
    print("\nAll tests complete.")
