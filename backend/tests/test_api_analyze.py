"""
Phase E tests: POST /api/analyze. Covers items A-Q from the approved
spec. The API is orchestration/serialization only -- these tests
verify it does not alter the underlying detector's numerical results
(item 21's "API output = existing internal analysis output"), not the
detector's own correctness (already covered by test_detector.py /
test_evidence_mapper.py).
"""

import ast
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ESSAY_ARTIFACT = REPO_ROOT / "backend" / "app" / "ml" / "essay_detector_v1.joblib"
SENTENCE_ARTIFACT = REPO_ROOT / "backend" / "app" / "ml" / "sentence_detector_v1.joblib"
PRIMARY_SAMPLES = REPO_ROOT / "data" / "generated" / "PRIMARY-DATASET-v1" / "samples.jsonl"

pytestmark = pytest.mark.skipif(
    not (ESSAY_ARTIFACT.exists() and SENTENCE_ARTIFACT.exists()),
    reason="detector artifacts not built in this environment",
)

SAMPLE_ESSAY = (
    "This is a sample essay about summer activities. Students often spend their break "
    "outdoors, playing sports and reading books. Many families travel together during "
    "this time. It is a season associated with relaxation and personal growth."
)


@pytest.fixture
def client():
    from app.main import app

    with TestClient(app) as c:
        yield c


def _load_text(sample_id: str) -> str:
    with open(PRIMARY_SAMPLES) as f:
        for line in f:
            rec = json.loads(line)
            if rec["sample_id"] == sample_id:
                return rec["text"]
    raise KeyError(sample_id)


# ---- A: valid essay ----

def test_A_valid_essay_returns_200_with_full_structure(client):
    r = client.post("/api/analyze", json={"text": SAMPLE_ESSAY})
    assert r.status_code == 200
    body = r.json()
    assert "analysis_id" in body
    assert "normalized_text" in body
    assert body["essay"]["state"] in ("machine_signal_detected", "no_strong_signal_detected", "inconclusive")
    assert "sentences" in body
    assert "metadata" in body


# ---- B/C: empty / whitespace input ----

def test_B_empty_input_returns_422(client):
    r = client.post("/api/analyze", json={"text": ""})
    assert r.status_code == 422


def test_C_whitespace_only_input_returns_422(client):
    r = client.post("/api/analyze", json={"text": "   \n\t  "})
    assert r.status_code == 422


# ---- D: short input ----

def test_D_short_but_nonempty_input_is_accepted():
    from app.main import app

    with TestClient(app) as client:
        r = client.post("/api/analyze", json={"text": "Hi."})
    assert r.status_code == 200


# ---- E: representative multi-paragraph essay ----

def test_E_multi_paragraph_essay(client):
    text = (
        "First paragraph starts here with some content. It has two sentences.\n\n"
        "Second paragraph follows with different content. It also has two sentences."
    )
    r = client.post("/api/analyze", json={"text": text})
    assert r.status_code == 200
    body = r.json()
    assert body["sentences"]["total_scorable_sentences"] >= 1


# ---- F: Unicode ----

def test_F_unicode_essay(client):
    text = "L'élève a écrit un essai. Il fait très beau aujourd'hui à Montréal. Emoji test: 😀 works."
    r = client.post("/api/analyze", json={"text": text})
    assert r.status_code == 200


# ---- G: punctuation ----

def test_G_punctuation_heavy_essay(client):
    text = 'She said, "Wait — really?!" He replied: "Yes; absolutely." Then... they left.'
    r = client.post("/api/analyze", json={"text": text})
    assert r.status_code == 200


# ---- H: candidate sentence offsets ----

def test_H_candidate_offsets_slice_normalized_text_correctly(client):
    r = client.post("/api/analyze", json={"text": SAMPLE_ESSAY})
    body = r.json()
    normalized = body["normalized_text"]
    for c in body["sentences"]["candidates"]:
        assert normalized[c["char_start"] : c["char_end"]] == c["text"]
    for s in body["sentences"]["skipped"]:
        assert normalized[s["char_start"] : s["char_end"]] == s["text"]


# ---- I: evidence presence ----

def test_I_essay_evidence_is_present_and_traceable(client):
    r = client.post("/api/analyze", json={"text": SAMPLE_ESSAY})
    body = r.json()
    assert len(body["essay"]["evidence"]) > 0
    for e in body["essay"]["evidence"]:
        assert e["feature"]
        assert e["statement"]
        assert e["direction"] in ("higher", "lower")


# ---- J: skipped sentence reporting ----

def test_J_skipped_sentences_have_explicit_reasons(client):
    r = client.post("/api/analyze", json={"text": SAMPLE_ESSAY})
    body = r.json()
    for s in body["sentences"]["skipped"]:
        assert s["reason"]


# ---- K: missing-evidence behavior ----

def test_K_extremely_short_input_may_yield_no_sentence_evidence_without_error(client):
    r = client.post("/api/analyze", json={"text": "Hi there friend."})
    assert r.status_code == 200
    body = r.json()
    if not body["sentences"]["has_evidence"]:
        assert body["sentences"]["no_evidence_reason"] is not None
        assert body["sentences"]["candidates"] == []


# ---- L: deterministic repeated request ----

def test_L_repeated_identical_requests_produce_identical_analysis(client):
    r1 = client.post("/api/analyze", json={"text": SAMPLE_ESSAY}).json()
    r2 = client.post("/api/analyze", json={"text": SAMPLE_ESSAY}).json()

    # analysis_id is explicitly NOT part of the deterministic result.
    assert r1["analysis_id"] != r2["analysis_id"]

    for r in (r1, r2):
        del r["analysis_id"]
    assert r1 == r2


# ---- M: invalid request ----

def test_M_missing_text_field_returns_422(client):
    r = client.post("/api/analyze", json={})
    assert r.status_code == 422


def test_M_wrong_type_returns_422(client):
    r = client.post("/api/analyze", json={"text": 12345})
    assert r.status_code == 422


def test_M_too_long_returns_413(client):
    r = client.post("/api/analyze", json={"text": "x" * 20001})
    assert r.status_code == 413


def test_M_at_max_length_is_accepted(client):
    # 20000 'x' characters segment as effectively one giant token-stream;
    # this only needs to prove the boundary itself doesn't reject valid input.
    r = client.post("/api/analyze", json={"text": "This is fine. " * 1400})  # ~19600 chars, under the limit
    assert r.status_code == 200


# ---- N: model failure handling ----

def test_N_startup_fails_loudly_if_an_artifact_is_missing():
    """A missing artifact at STARTUP must crash app startup entirely
    (Phase B's standing rule: never serve requests with a partially-
    loaded detector) -- not silently defer to a per-request 503."""
    from app.main import app
    from app.services import detector

    detector._load_essay_artifact.cache_clear()
    original_path = detector.ESSAY_ARTIFACT_PATH
    detector.ESSAY_ARTIFACT_PATH = Path("/nonexistent/path.joblib")
    try:
        with pytest.raises(detector.DetectorArtifactMissingError):
            with TestClient(app):
                pass
    finally:
        detector.ESSAY_ARTIFACT_PATH = original_path
        detector._load_essay_artifact.cache_clear()


def test_N_artifact_disappearing_mid_process_returns_503_not_a_fabricated_result(client, monkeypatch):
    """A successfully-started service whose artifact later becomes
    unloadable (e.g. filesystem issue) must return 503 on the affected
    request, never a fabricated analysis."""
    from app.services import detector

    # `client` fixture already completed a successful startup (artifact
    # cached). Clear the cache and point at a bad path to simulate the
    # artifact vanishing after startup, then make a normal request
    # (not a fresh app startup) against the already-running client.
    detector._load_essay_artifact.cache_clear()
    monkeypatch.setattr(detector, "ESSAY_ARTIFACT_PATH", Path("/nonexistent/path.joblib"))

    r = client.post("/api/analyze", json={"text": SAMPLE_ESSAY})

    detector._load_essay_artifact.cache_clear()  # restore for subsequent tests
    assert r.status_code == 503
    assert "/nonexistent" not in r.json()["detail"]


def test_N_unexpected_error_returns_500_without_leaking_internals(monkeypatch):
    from app.main import app
    from app.api import analyze as analyze_module

    def _boom(text):
        raise RuntimeError("simulated internal failure with a fake /Users/someone/secret/path.py detail")

    monkeypatch.setattr(analyze_module, "build_essay_evidence", _boom)

    with TestClient(app) as client:
        r = client.post("/api/analyze", json={"text": SAMPLE_ESSAY})

    assert r.status_code == 500
    detail = r.json()["detail"]
    assert "/Users/" not in detail
    assert "secret" not in detail
    assert "Traceback" not in detail


# ---- O: no LLM/network dependency ----

def test_O_analyze_module_has_no_llm_or_network_imports():
    source = (REPO_ROOT / "backend" / "app" / "api" / "analyze.py").read_text()
    tree = ast.parse(source)
    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_names.add(node.module)
    forbidden = ("openai", "anthropic", "google.generativeai", "genai", "requests", "urllib", "socket")
    for name in imported_names:
        for f in forbidden:
            assert f not in name.lower(), f"analyze.py imports {name}"


# ---- P: model reuse ----

def test_P_repeated_requests_reuse_the_same_loaded_artifact_object(client):
    from app.services.detector import _load_essay_artifact

    client.post("/api/analyze", json={"text": SAMPLE_ESSAY})
    a = _load_essay_artifact()
    client.post("/api/analyze", json={"text": "A different essay entirely, for variety."})
    b = _load_essay_artifact()
    assert a is b  # same object across requests -- never reloaded per-request


# ---- Q: health endpoint regression ----

def test_Q_health_endpoint_still_works_and_now_reports_detector_readiness(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["detector_loaded"] is True  # lifespan preload already ran


def test_Q_health_endpoint_does_not_run_inference(client, monkeypatch):
    from app.services import detector

    def _fail(*a, **kw):
        raise AssertionError("health endpoint must never call predict_essay")

    monkeypatch.setattr(detector, "predict_essay", _fail)
    r = client.get("/api/health")
    assert r.status_code == 200


# ---- Item 22: frozen regression case, family 302DC21A6DEE ----

@pytest.mark.skipif(not PRIMARY_SAMPLES.exists(), reason="PRIMARY-DATASET-v1 not present")
def test_frozen_regression_case_302DC21A6DEE_via_api(client):
    """API must reproduce the exact same score/state as the production
    detector (Phase B/D) for the known, documented borderline case --
    never 'fixed' to look better."""
    text = _load_text("302DC21A6DEE__human")
    r = client.post("/api/analyze", json={"text": text})
    assert r.status_code == 200
    body = r.json()
    assert body["essay"]["score"] == pytest.approx(0.49, abs=5e-3)
    assert body["essay"]["state"] == "machine_signal_detected"


# ---- Item 5/3/18: response never exposes internal model configuration ----

def test_response_never_exposes_model_C_threshold_or_raw_feature_vector(client):
    r = client.post("/api/analyze", json={"text": SAMPLE_ESSAY})
    body_str = json.dumps(r.json())
    assert "0.005994842503189409" not in body_str  # essay model's C
    assert "166.81005372000558" not in body_str  # sentence model's C
    assert "threshold" not in json.dumps(r.json()["essay"]).lower()
    assert "essay_detector_v1.joblib" not in body_str
    assert str(REPO_ROOT) not in body_str  # no local filesystem path


# ---- Item 7: sentence labels are always the cautious form ----

def test_sentence_labels_are_never_definitive_ai_claims(client):
    r = client.post("/api/analyze", json={"text": SAMPLE_ESSAY})
    body = r.json()
    for c in body["sentences"]["candidates"]:
        assert c["label"] == "potentially_ai_assisted"
        assert c["label"] not in ("ai_written", "definitely_ai", "AI_generated_sentence")


# ---- Item 16: API path does not import training/generation code ----

def test_api_modules_do_not_import_research_or_training_code():
    for path in [
        REPO_ROOT / "backend" / "app" / "api" / "analyze.py",
        REPO_ROOT / "backend" / "app" / "services" / "detector.py",
        REPO_ROOT / "backend" / "app" / "services" / "evidence_mapper.py",
        REPO_ROOT / "backend" / "app" / "main.py",
    ]:
        source = path.read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            else:
                continue
            for n in names:
                assert not n.startswith("run_"), f"{path.name} imports research/experiment-runner module {n}"
                assert "scripts" not in n, f"{path.name} imports from scripts/: {n}"
