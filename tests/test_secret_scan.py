import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "check_secrets.py"
SPEC = importlib.util.spec_from_file_location("check_secrets", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
check_secrets = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_secrets)


def test_unapproved_binary_documents_are_rejected(
    monkeypatch,
    tmp_path: Path,
) -> None:
    suspicious = tmp_path / "Robokassa.docx"
    suspicious.write_bytes(b"not-a-real-docx")
    allowed = tmp_path / "docs/final/Tik_Tok_Loader_Unified_Specification.pdf"
    allowed.parent.mkdir(parents=True)
    allowed.write_bytes(b"not-a-real-pdf")
    monkeypatch.setattr(check_secrets, "ROOT", tmp_path)
    monkeypatch.setattr(check_secrets, "candidate_files", lambda: [suspicious, allowed])

    assert check_secrets.unexpected_binary_documents() == ["Robokassa.docx"]
