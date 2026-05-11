"""Test startup diagnostics."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'daily_intel'))

def test_diag_runs():
    from trevor_diag import run
    results = run()
    assert len(results) > 0
    print(f"  ✅ diagnostics: {len(results)} checks run")

if __name__ == "__main__":
    test_diag_runs()
    print("\nAll diagnostic tests passed ✅")
