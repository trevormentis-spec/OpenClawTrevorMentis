"""Test trevor_fonts module."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'daily_intel'))

def test_fonts_register():
    from trevor_fonts import register_fonts
    reg = register_fonts()
    assert len(reg) >= 5  # at least 5 font names
    print(f"  ✅ fonts: {len(reg)} registered")

def test_font_fallback():
    from trevor_fonts import get_font_path
    path = get_font_path("Display")
    assert path is not None
    print(f"  ✅ font fallback: {path}")

if __name__ == "__main__":
    test_fonts_register()
    test_font_fallback()
    print("\nAll font tests passed ✅")
