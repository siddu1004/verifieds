from pathlib import Path
import pytest
from verifieds.detector.engine import analyze_file
from verifieds.detector.loader import load_rules

ROOT = Path(__file__).resolve().parent.parent


def test_rule_loader():
    rules = load_rules()
    assert len(rules) == 4
    rule_ids = {r["rule_id"] for r in rules}
    assert rule_ids == {
        "array-queue-front-removal",
        "linear-min-extract",
        "adjacent-swap-sort",
        "linear-search-in-loop",
    }


@pytest.mark.parametrize(
    "rule_id",
    [
        "array-queue-front-removal",
        "linear-min-extract",
        "adjacent-swap-sort",
        "linear-search-in-loop",
    ],
)
def test_rule_fixtures(rule_id: str):
    fixture_dir = ROOT / "tests" / "fixtures" / rule_id
    assert fixture_dir.exists(), f"Missing fixture dir for {rule_id}"

    pos_files = list(fixture_dir.glob("pos_*.cpp"))
    neg_files = list(fixture_dir.glob("neg_*.cpp"))

    assert len(pos_files) >= 2, f"{rule_id} requires >= 2 positive fixtures"
    assert len(neg_files) >= 2, f"{rule_id} requires >= 2 negative fixtures"

    for pos in pos_files:
        findings = analyze_file(pos)
        rule_findings = [f for f in findings if f.rule_id == rule_id]
        assert len(rule_findings) == 1, (
            f"Expected 1 finding for {pos.name}, got {len(rule_findings)}"
        )

    for neg in neg_files:
        findings = analyze_file(neg)
        rule_findings = [f for f in findings if f.rule_id == rule_id]
        assert len(rule_findings) == 0, (
            f"Expected 0 findings for {neg.name}, got {len(rule_findings)}"
        )


def test_array_ready_queue_detection():
    target = ROOT / "sim" / "src" / "ReadyQueue.hpp"
    findings = analyze_file(target)

    rules_found = {f.rule_id for f in findings}
    assert "linear-min-extract" in rules_found
    assert "array-queue-front-removal" in rules_found


def test_heap_ready_queue_clean():
    min_heap = ROOT / "sim" / "src" / "MinHeap.hpp"

    # Inspect HeapReadyQueue and MinHeap specifically
    findings_heap = analyze_file(min_heap)
    assert len(findings_heap) == 0


def test_scanner_edge_cases(tmp_path: Path):
    from verifieds.detector.scanner import SourceView

    code = """
    // Comment with "quoted string" and /* nested comment */
    /* Multi-line
       comment */
    void foo() {
        std::string s = "string with /* comment */ and \\"escaped quotes\\"";
        for (int i = 0; i < 10; ++i)
            do_something(i);
        while (unclosed_header
        for (int j = 0; j < 5; ++j) {
            unclosed_body
    """
    sf = tmp_path / "test.cpp"
    sf.write_text(code, encoding="utf-8")
    sv = SourceView(code)
    assert len(sv.tokens) > 0
    assert len(sv.loops) >= 1
    findings = analyze_file(sf)
    assert isinstance(findings, list)


def test_loader_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import verifieds.detector.loader as loader_mod

    # Missing rules dir
    monkeypatch.setattr(loader_mod, "RULES_DIR", tmp_path / "nonexistent")
    with pytest.raises(FileNotFoundError, match="Rules directory not found"):
        loader_mod.load_rules()

    # Missing matcher py file
    rdir = tmp_path / "rules"
    fdir = tmp_path / "fixtures"
    rdir.mkdir()
    fdir.mkdir()
    (rdir / "bad_rule.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(loader_mod, "RULES_DIR", rdir)
    monkeypatch.setattr(loader_mod, "FIXTURES_DIR", fdir)
    with pytest.raises(FileNotFoundError, match="Missing rule matcher script"):
        loader_mod.load_rules()

    # Missing fixture dir
    (rdir / "bad_rule.py").write_text("def match(sv): return []", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="Missing fixture directory"):
        loader_mod.load_rules()

    # Missing pos/neg fixtures
    fix_bad = fdir / "bad_rule"
    fix_bad.mkdir()
    with pytest.raises(FileNotFoundError, match="must have pos_\\*\\.cpp"):
        loader_mod.load_rules()

    # Missing match function in python file
    (fix_bad / "pos_1.cpp").write_text("int main(){}", encoding="utf-8")
    (fix_bad / "neg_1.cpp").write_text("int main(){}", encoding="utf-8")
    (rdir / "bad_rule.py").write_text("x = 1", encoding="utf-8")
    with pytest.raises(AttributeError, match="must define a match"):
        loader_mod.load_rules()
