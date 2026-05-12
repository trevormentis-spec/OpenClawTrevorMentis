"""Test FTS5 memory store."""
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'daily_intel'))

def test_memory_basic():
    from trevor_memory import MemoryStore
    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.db')
    os.close(tmp_fd)
    try:
        mem = MemoryStore(tmp_path)
        mem.index("narrative", "test content", key="t1", region="europe")
        assert mem.count("narrative") == 1
        results = mem.search("test")
        assert len(results) >= 1
        prior = mem.get_previous_narrative("europe", days=30)
        assert prior is not None
        mem.close()
        print(f"  ✅ memory: basic CRUD works")
    finally:
        os.unlink(tmp_path)

def test_memory_export_import():
    from trevor_memory import MemoryStore
    tmp_fd1, tmp1 = tempfile.mkstemp(suffix='.db')
    tmp_fd2, tmp2 = tempfile.mkstemp(suffix='.db')
    os.close(tmp_fd1); os.close(tmp_fd2)
    export_path = tempfile.mktemp(suffix='.json')
    try:
        mem1 = MemoryStore(tmp1)
        mem1.index("narrative", "export test", key="export1", region="test")
        mem1.export_snapshot(export_path)
        mem2 = MemoryStore(tmp2)
        count = mem2.import_snapshot(export_path)
        assert count == 1
        assert mem2.count() == 1
        mem1.close(); mem2.close()
        print(f"  ✅ memory: export/import works")
    finally:
        for p in [tmp1, tmp2, export_path]:
            try: os.unlink(p)
            except: pass

if __name__ == "__main__":
    test_memory_basic()
    test_memory_export_import()
    print("\nAll memory tests passed ✅")
