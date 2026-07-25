from pathlib import Path

from typer.testing import CliRunner

from prosebench.cli import app

runner = CliRunner()


def test_assess_cli_local(tmp_path: Path) -> None:
    source = tmp_path / "essay.md"
    source.write_text(
        "A problem needs a decision.\n\nFor example, one option costs 42 dollars.",
        encoding="utf-8",
    )
    output_dir = tmp_path / "reports"
    result = runner.invoke(
        app,
        [
            "assess",
            str(source),
            "--provider",
            "local",
            "--output-dir",
            str(output_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (output_dir / "essay-assessment.md").exists()
    assert (output_dir / "essay-assessment.html").exists()
    assert (output_dir / "essay-assessment.json").exists()


def test_profiles_cli() -> None:
    result = runner.invoke(app, ["profiles"])
    assert result.exit_code == 0, result.output
    assert "academic_argument" in result.output
    assert "professional_prose" in result.output
