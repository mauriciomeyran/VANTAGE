"""
Cobertura conductual url_gate.py — ≥90% stmts, cero Notion (fakes/mocks).
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "Layer_1" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import url_gate  # noqa: E402
from url_gate import (  # noqa: E402
    AGREGADOR_DOMAINS,
    is_agregador,
    normalize_url,
    validate_url_offline,
    validate_url_pre_ingestion,
)


# ── is_agregador ─────────────────────────────────────────────────────────────

def test_is_agregador_empty_and_none():
    """L34: url falsy → False."""
    assert is_agregador("") is False
    assert is_agregador(None) is False  # type: ignore[arg-type]


def test_is_agregador_known_domains():
    assert is_agregador("https://www.linkedin.com/jobs/view/1")
    assert is_agregador("https://mx.indeed.com/viewjob?jk=x")
    assert is_agregador("https://jobs.nike.com/job/1")
    assert is_agregador("https://boards.greenhouse.io/co/jobs/1")
    assert is_agregador("https://jobs.lever.co/co/abc")
    assert is_agregador("https://apply.workable.com/co/j/1")
    assert not is_agregador("https://careers.zara.com/job/1")


def test_is_agregador_urlparse_exception():
    """L38-39: urlparse lanza → False."""
    with patch("url_gate.urllib.parse.urlparse", side_effect=ValueError("boom")):
        assert is_agregador("https://indeed.com/x") is False


# ── normalize_url ────────────────────────────────────────────────────────────

def test_normalize_url_empty_and_non_str():
    """L49: empty / non-str passthrough."""
    assert normalize_url("") == ""
    assert normalize_url(None) is None  # type: ignore[arg-type]
    assert normalize_url(123) == 123  # type: ignore[arg-type]


def test_normalize_url_adds_https_and_preserves():
    assert normalize_url("example.com/job") == "https://example.com/job"
    assert normalize_url("  example.com/j  ") == "https://example.com/j"
    assert normalize_url("https://ok.com") == "https://ok.com"
    assert normalize_url("http://ok.com") == "http://ok.com"


# ── validate_url_offline ─────────────────────────────────────────────────────

def test_offline_jd_already_exists():
    """L70: JD > 100 chars → válido sin mirar URL."""
    jd = "x" * 101
    ok, reason = validate_url_offline("", jd_text=jd)
    assert ok is True
    assert reason == "JD_ALREADY_EXISTS"
    # strip cuenta
    ok, reason = validate_url_offline("https://x.com", jd_text="  " + "y" * 101 + "  ")
    assert ok and reason == "JD_ALREADY_EXISTS"


def test_offline_missing_url():
    ok, reason = validate_url_offline("")
    assert ok is False and reason == "MISSING_URL"


def test_offline_agregador_valid():
    ok, reason = validate_url_offline("https://www.linkedin.com/jobs/view/9")
    assert ok is True and reason == "AGREGADOR_VALID"


def test_offline_tracking_blocked():
    for bad in (
        "https://x.com/j?utm_source=1",
        "https://x.com/j?gclid=abc",
        "https://x.com/j?fbclid=1",
        "https://x.com/j?ref=home",
        "https://x.com/j?source=email",
    ):
        ok, reason = validate_url_offline(bad)
        assert ok is False and reason == "TRACKING_URL", bad


def test_offline_valid_https():
    ok, reason = validate_url_offline("https://careers.example.com/job/1")
    assert ok is True and reason == "VALID"


def test_offline_invalid_scheme_after_normalize_edge():
    """L84: si tras normalize no hay http(s) → INVALID_SCHEME.
    Fuerza normalize a devolver string sin esquema (rama defensiva).
    """
    with patch("url_gate.normalize_url", return_value="not-a-url"):
        # no agregador, no tracking
        ok, reason = validate_url_offline("whatever")
        assert ok is False and reason == "INVALID_SCHEME"


# ── validate_url_pre_ingestion ───────────────────────────────────────────────

def test_pre_ingestion_jd_and_missing():
    """L94, L97."""
    ok, reason = validate_url_pre_ingestion("", jd_text="z" * 101)
    assert ok is True and reason == "JD_ALREADY_EXISTS"
    ok, reason = validate_url_pre_ingestion("")
    assert ok is False and reason == "MISSING_URL"


def test_pre_ingestion_import_error_falls_to_offline():
    """L103-104: sin requests → offline."""
    import builtins
    real_import = builtins.__import__

    def _no_requests(name, *args, **kwargs):
        if name == "requests" or name.startswith("requests."):
            raise ImportError("no requests")
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=_no_requests):
        ok, reason = validate_url_pre_ingestion("https://careers.zara.com/job/1")
        assert ok is True and reason == "VALID"


def test_pre_ingestion_agregador_head_200():
    """L107-120: HEAD 200 → AGREGADOR_VERIFIED."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_requests = MagicMock()
    mock_requests.head.return_value = mock_resp
    mock_requests.exceptions.RequestException = Exception

    with patch.dict(sys.modules, {"requests": mock_requests}):
        # re-import path uses import inside function
        ok, reason = validate_url_pre_ingestion("https://indeed.com/viewjob?jk=1")
    assert ok is True
    assert reason == "AGREGADOR_VERIFIED"
    mock_requests.head.assert_called()


def test_pre_ingestion_agregador_head_non_200():
    """L121: status != 200 → AGREGADOR_RETRY_STATUS_*."""
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_requests = MagicMock()
    mock_requests.head.return_value = mock_resp
    mock_requests.exceptions.RequestException = type("ReqExc", (Exception,), {})

    with patch.dict(sys.modules, {"requests": mock_requests}):
        ok, reason = validate_url_pre_ingestion("https://www.linkedin.com/jobs/view/2")
    assert ok is True
    assert reason == "AGREGADOR_RETRY_STATUS_403"


def test_pre_ingestion_agregador_head_timeout():
    """L122-124: RequestException → AGREGADOR_RETRY_TIMEOUT."""
    ReqExc = type("RequestException", (Exception,), {})
    mock_requests = MagicMock()
    mock_requests.exceptions.RequestException = ReqExc
    mock_requests.head.side_effect = ReqExc("timeout")

    with patch.dict(sys.modules, {"requests": mock_requests}):
        ok, reason = validate_url_pre_ingestion("https://computrabajo.com.mx/ofertas/1")
    assert ok is True
    assert reason == "AGREGADOR_RETRY_TIMEOUT"


def test_pre_ingestion_whitelisted_career_domains():
    """L132-134: jobs.nike / workable / greenhouse / lever whitelist."""
    mock_requests = MagicMock()
    # not agregador path for plain domain check — nike is in AGREGADOR so hits agg first.
    # Use workable via non-agg? workable IS agregador. Whitelist runs only if NOT agregador.
    # So whitelist is for when is_agregador is False but domain contains pattern.
    # Looking at code: whitelist is AFTER agregador block. So for agregador URLs
    # we never reach whitelist. To hit L132-134, URL must NOT be agregador but
    # domain contains problematic substring — e.g. subdomain not matching endswith
    # wait: workable.com IS in AGREGADOR_DOMAINS so is_agregador True.
    # To hit whitelist we need is_agregador False. The patterns are the same list...
    # jobs.nike.com is in AGREGADOR_DOMAINS. So whitelist is dead for those domains
    # unless is_agregador fails somehow.
    # Force is_agregador False to reach whitelist:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_requests.head.return_value = mock_resp
    mock_requests.exceptions.RequestException = Exception

    with patch.dict(sys.modules, {"requests": mock_requests}):
        with patch("url_gate.is_agregador", return_value=False):
            for host, key in (
                ("jobs.nike.com", "jobs.nike.com"),
                ("boards.workable.com", "workable.com"),
                ("boards.greenhouse.io", "greenhouse.io"),
                ("jobs.lever.co", "lever.co"),
            ):
                ok, reason = validate_url_pre_ingestion(f"https://{host}/job/1")
                assert ok is True, host
                assert reason == f"WHITELISTED_DOMAIN_{key}", (host, reason)


def test_pre_ingestion_whitelist_urlparse_exception():
    """L135-136: urlparse exception in whitelist → fall through offline."""
    mock_requests = MagicMock()
    mock_requests.exceptions.RequestException = Exception
    with patch.dict(sys.modules, {"requests": mock_requests}):
        with patch("url_gate.is_agregador", return_value=False):
            with patch("url_gate.urllib.parse.urlparse", side_effect=RuntimeError("x")):
                ok, reason = validate_url_pre_ingestion("https://careers.example.com/j")
    assert ok is True and reason == "VALID"


def test_pre_ingestion_fallback_offline_non_agg():
    """L139: resto → validate_url_offline."""
    mock_requests = MagicMock()
    mock_requests.exceptions.RequestException = Exception
    with patch.dict(sys.modules, {"requests": mock_requests}):
        with patch("url_gate.is_agregador", return_value=False):
            ok, reason = validate_url_pre_ingestion("https://careers.zara.com/job/99")
    assert ok is True and reason == "VALID"


def test_agregador_domains_list_nonempty():
    assert "linkedin.com" in AGREGADOR_DOMAINS
    assert "indeed.com" in AGREGADOR_DOMAINS
