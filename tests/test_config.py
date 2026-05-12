"""Test trevor_config module."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'daily_intel'))

def test_config_imports():
    from trevor_config import WORKSPACE, EXPORTS_DIR, THEATRES, THEATRE_KEYS
    assert WORKSPACE is not None
    assert EXPORTS_DIR is not None
    assert len(THEATRES) >= 6
    assert len(THEATRE_KEYS) >= 6
    print(f"  ✅ config: {len(THEATRES)} theatres, WORKSPACE exists: {WORKSPACE.exists()}")

def test_theatre_keys_match():
    from trevor_config import THEATRES, THEATRE_KEYS
    assert len(THEATRES) == len(THEATRE_KEYS)
    for t in THEATRES:
        assert t["key"] in THEATRE_KEYS
    print(f"  ✅ theatre keys: {len(THEATRE_KEYS)} match")

def test_logger_creates():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'daily_intel'))
    from trevor_log import get_logger
    log = get_logger("test")
    log.info("test message", component="test")
    print(f"  ✅ logger: creates and logs")

if __name__ == "__main__":
    test_config_imports()
    test_theatre_keys_match()
    test_logger_creates()
    print("\nAll config tests passed ✅")
