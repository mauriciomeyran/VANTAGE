"""
test_linkedin_identity_matcher.py — Phase 3C
Employer identity matcher: matriz de comportamiento + regresiones Phase 3B.

Cada test traza a una regla canónica. La trazabilidad se verifica en
test_rule_to_test_map_is_complete (todo test declarado existe y corre).
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import pytest  # noqa: E402
from linkedin_identity_matcher import (  # noqa: E402
    BLOCKED_EMPLOYERS, CANONICAL_RULE_MAP, RULE_TO_TEST, EmployerIdentityInput,
    MatchBasis, MatchStatus, match_employer, normalize_identity,
    resolve_employer_identity,
)


# ===========================================================================
# M01 — Employer exactamente coincide con blocked employer → BLOCKED
# RULES §2 + §8
# ===========================================================================
def test_m01_employer_exactly_matches_blocked():
    r = match_employer(EmployerIdentityInput(observed_employer="L'Oréal"))
    assert r.match_status == MatchStatus.BLOCKED
    assert r.employer_match is True
    assert r.employer_identity == "l'oreal"   # normalización sin acentos
    assert MatchBasis.IDENTITY_EXACT_MATCH in r.match_basis
    assert r.blocked_identity_matched == "L'Oréal"


def test_m01b_each_blocked_employer_blocks():
    for name in sorted(BLOCKED_EMPLOYERS):
        r = match_employer(EmployerIdentityInput(observed_employer=name))
        assert r.match_status == MatchStatus.BLOCKED, name
        assert r.employer_match is True, name


# ===========================================================================
# M02 — Employer claramente distinto → NOT_BLOCKED
# RULES §2
# ===========================================================================
def test_m02_employer_clearly_distinct():
    for name in ("Benefit Cosmetics", "Suntory Global Spirits", "PepsiCo",
                 "Philip Morris International", "Saint Laurent", "Cartier"):
        r = match_employer(EmployerIdentityInput(observed_employer=name))
        assert r.match_status == MatchStatus.NOT_BLOCKED, name
        assert r.employer_match is False, name
        assert MatchBasis.IDENTITY_NO_MATCH in r.match_basis


# ===========================================================================
# M03 — Blocked employer aparece únicamente como retail channel → NOT_BLOCKED
# RULES §2 (channel no activa el veto) + PROMPT §8
# ===========================================================================
def test_m03_blocked_employer_only_as_retail_channel():
    r = match_employer(EmployerIdentityInput(
        observed_employer="Benefit Cosmetics",
        observed_retail_channel="El Palacio de Hierro"))
    assert r.match_status == MatchStatus.NOT_BLOCKED
    assert r.employer_match is False
    assert r.employer_identity == "benefit cosmetics"
    assert MatchBasis.CHANNEL_FIELDS_EXCLUDED in r.match_basis
    assert MatchBasis.IDENTITY_EXACT_MATCH not in r.match_basis
    assert r.blocked_identity_matched is None


# ===========================================================================
# M04 — Blocked employer aparece únicamente como client → NOT_BLOCKED
# RULES §2
# ===========================================================================
def test_m04_blocked_employer_only_as_client():
    r = match_employer(EmployerIdentityInput(
        observed_employer="Cartier", observed_client="Dockers"))
    assert r.match_status == MatchStatus.NOT_BLOCKED
    assert r.employer_match is False
    assert MatchBasis.CHANNEL_FIELDS_EXCLUDED in r.match_basis


# ===========================================================================
# M05 — Blocked employer aparece únicamente como distribution partner
# RULES §2
# ===========================================================================
def test_m05_blocked_employer_only_as_distribution_partner():
    r = match_employer(EmployerIdentityInput(
        observed_employer="Sanborns",
        observed_distribution_partner="El Palacio de Hierro"))
    assert r.match_status == MatchStatus.NOT_BLOCKED
    assert r.employer_match is False


# ===========================================================================
# M06 — Employer + texto no relacionado contiene nombre blocked
# → sin bloqueo por substring
# PROMPT §8 (no substring-only matching)
# ===========================================================================
def test_m06_unrelated_text_containing_blocked_name():
    # El nombre blocked aparece como texto libre dentro del nombre del employer,
    # como token NO inicial ni exacto → no debe BLOQUEAR por substring.
    for name in ("Grupo Palacio Textil", "Palacio Textil",
                 "Puerto de Liverpool"):
        r = match_employer(EmployerIdentityInput(observed_employer=name))
        assert r.employer_match is False, name
        assert r.match_status in (MatchStatus.NOT_BLOCKED, MatchStatus.AMBIGUOUS), name


def test_no_substring_only_matching_anywhere():
    """Ninguna forma de blocked embebido arbitrariamente bloquea."""
    sneaky = [
        "Mi Dockers Favorito", "Todo L'Oreal Outlet", "X Levis Store",
        "Mejor Palacio de Hierro Bar", "sdjfhsdkfjhsdkjfh", "12345",
    ]
    for name in sneaky:
        r = match_employer(EmployerIdentityInput(observed_employer=name))
        assert r.employer_match is False, name


# ===========================================================================
# M07 — Employer identity match con variante válida de identidad → BLOCKED
# RULES §2 (identidad canónica: variantes normalizan a la misma entidad)
# ===========================================================================
def test_m07_identity_variant_blocked():
    # Cada variante debe ser trazable a RULES §2 ("identidad canónica"):
    # sólo se aceptan formas de la MISMA entidad bloqueada — con/sin acento,
    # con/sin artículo inicial, con/sin designador legal, con/sin variante
    # geográfica. NO se aceptan entidades distintas que contengan el nombre
    # blocked como substring (eso es M06/M08, no M07).
    variants = [
        "L'Oréal", "L'Oreal", "L'OREAL", "L'Oréal Mexico", "L'Oréal México",
        "L'Oréal Mexico S.A. de C.V.", "L'Oreal Mexico SA de CV",
        "L'Oréal Mexico S.A.S. de C.V.",
        "Levi Strauss & Co", "Levi Strauss", "Levi Strauss and Company",
        "Levi's", "LEVI STRAUSS MEXICO",
        "El Palacio de Hierro", "Palacio de Hierro",
    ]
    for name in variants:
        r = match_employer(EmployerIdentityInput(observed_employer=name))
        assert r.match_status == MatchStatus.BLOCKED, f"{name} → {r.match_status}"
        assert r.employer_match is True, name


# ===========================================================================
# M08 — Identidad ambigua → NO inferir BLOCKED
# PROMPT §8 (identity-based; sin inferencia sobre ambigüedad)
# ===========================================================================
def test_m08_ambiguous_identity_not_inferred():
    # "Dockers Heroico" comparte el token inicial con el blocked "Dockers"
    # pero no ES la identidad bloqueada → AMBIGUOUS, employer_match False.
    for name in ("Dockers Heroico", "L'Oreal Outlet Store"):
        r = match_employer(EmployerIdentityInput(observed_employer=name))
        assert r.employer_match is False, name
        assert r.match_status in (MatchStatus.AMBIGUOUS, MatchStatus.NOT_BLOCKED), name
        if r.match_status == MatchStatus.AMBIGUOUS:
            assert MatchBasis.AMBIGUOUS_PARTIAL_OVERLAP in r.match_basis


def test_m08b_ambiguous_reports_candidate_without_blocking():
    r = match_employer(EmployerIdentityInput(observed_employer="Dockers Heroico"))
    if r.match_status == MatchStatus.AMBIGUOUS:
        assert r.blocked_identity_matched == "Dockers"
        assert r.employer_match is False


# ===========================================================================
# M09 — Evidencia de employer ausente → no inferir identidad
# PROMPT §5 (value null + NOT_OBSERVED; no inferencia)
# ===========================================================================
def test_m09_missing_employer_evidence():
    for value in (None, "", "   "):
        r = match_employer(EmployerIdentityInput(observed_employer=value))
        assert r.match_status == MatchStatus.UNRESOLVED
        assert r.employer_match is False
        assert r.employer_identity is None
        assert MatchBasis.EMPLOYER_EVIDENCE_MISSING in r.match_basis


def test_m09b_channel_only_evidence_does_not_become_employer():
    """Sólo hay canal; no se infiere employer a partir del canal."""
    r = match_employer(EmployerIdentityInput(
        observed_employer=None,
        observed_retail_channel="El Palacio de Hierro"))
    assert r.match_status == MatchStatus.UNRESOLVED
    assert r.employer_identity is None
    assert r.employer_match is False
    assert MatchBasis.CHANNEL_FIELDS_EXCLUDED in r.match_basis


# ===========================================================================
# M10 — Employer identity + mención de canal no relacionado
# → employer identity tiene precedencia
# RULES §2
# ===========================================================================
def test_m10_employer_takes_precedence_over_channel():
    r = match_employer(EmployerIdentityInput(
        observed_employer="Cartier",
        observed_retail_channel="El Palacio de Hierro",
        observed_brand="INTRANT",
        observed_client="Sephora"))
    assert r.employer_identity == "cartier"
    assert r.employer_match is False
    assert r.match_status == MatchStatus.NOT_BLOCKED
    # El canal blocked queda registrado pero no altera el veredicto.
    assert r.excluded_channel_mentions["retail_channel"] == "El Palacio de Hierro"


def test_m10b_blocked_employer_wins_over_clean_channel():
    """Si el EMPLOYER es blocked, ningún canal limpio lo salva."""
    r = match_employer(EmployerIdentityInput(
        observed_employer="Levi Strauss",
        observed_retail_channel="Liverpool"))
    assert r.match_status == MatchStatus.BLOCKED
    assert r.employer_match is True


# ===========================================================================
# REGRESIONES Phase 3B
# ===========================================================================

def test_regression_rmatch_01_benefit_channel_palacio():
    """R-MATCH-01: Benefit Cosmetics + canal El Palacio de Hierro."""
    r = match_employer(EmployerIdentityInput(
        observed_employer="Benefit Cosmetics",
        observed_retail_channel="El Palacio de Hierro"))
    assert r.employer_identity == "benefit cosmetics"
    assert r.excluded_channel_mentions["retail_channel"] == "El Palacio de Hierro"
    assert r.match_status == MatchStatus.NOT_BLOCKED
    assert r.employer_match is False


def test_regression_rmatch_02_levi_strauss_employer_dockers_brand():
    """R-MATCH-02: employer Levi Strauss & Co; brand DOCKERS HEROS.

    Debe quedar explícito cuál campo es la employer identity y cuál es brand.
    """
    r = match_employer(EmployerIdentityInput(
        observed_employer="Levi Strauss & Co",
        observed_brand="DOCKERS HEROS"))
    # Employer identity viene SÓLO del campo employer.
    assert r.employer_identity == "levi strauss"
    assert MatchBasis.EMPLOYER_FIELD_AUTHORITATIVE in r.match_basis
    assert r.excluded_channel_mentions["brand"] == "DOCKERS HEROS"
    # El match se trazabiliza a la identidad exacta del employer.
    assert r.match_status == MatchStatus.BLOCKED
    assert r.employer_match is True
    assert r.blocked_identity_matched == "Levi Strauss"
    assert MatchBasis.IDENTITY_EXACT_MATCH in r.match_basis


def test_regression_rmatch_02b_dockers_brand_alone_does_not_block():
    """La marca DOCKERS HEROS como brand no activa veto por sí sola."""
    r = match_employer(EmployerIdentityInput(
        observed_employer="Sanborns", observed_brand="DOCKERS HEROS"))
    assert r.employer_match is False
    assert r.match_status == MatchStatus.NOT_BLOCKED


# ===========================================================================
# DETERMINISMO (§8 del spec)
# ===========================================================================
def test_determinism_same_input_same_output():
    cases = [
        EmployerIdentityInput(observed_employer="L'Oréal"),
        EmployerIdentityInput(observed_employer="Benefit Cosmetics",
                              observed_retail_channel="El Palacio de Hierro"),
        EmployerIdentityInput(observed_employer="Levi Strauss & Co",
                              observed_brand="DOCKERS HEROS"),
        EmployerIdentityInput(observed_employer=None),
        EmployerIdentityInput(observed_employer="Dockers Heroico"),
    ]
    for case in cases:
        results = [match_employer(case).to_json() for _ in range(5)]
        assert all(r == results[0] for r in results), case


def test_determinism_order_independent():
    """El orden de blocked_employer_set no altera el veredicto."""
    a = frozenset({"L'Oréal", "Levi Strauss"})
    b = frozenset({"L'Oréal", "Levi Strauss"})
    for name in ("L'Oréal", "Cartier"):
        r1 = match_employer(EmployerIdentityInput(observed_employer=name,
                                                   blocked_employer_set=a))
        r2 = match_employer(EmployerIdentityInput(observed_employer=name,
                                                   blocked_employer_set=b))
        assert r1.match_status == r2.match_status
        assert r1.employer_match == r2.employer_match


def test_normalization_is_pure_and_idempotent():
    for raw in ("L'Oréal Mexico S.A. de C.V.", "Levi Strauss & Co", "Dockers"):
        once = normalize_identity(raw)
        twice = normalize_identity(once)
        assert once == twice
        assert resolve_employer_identity(raw) == once


# ===========================================================================
# TRAZABILIDAD Y CONTROL DE CAMBIOS (§9 del spec)
# ===========================================================================
def test_rule_to_test_map_is_complete():
    """Todo test declarado en RULE_TO_TEST existe en el módulo."""
    import inspect
    src = Path(__file__).read_text()
    for rule, tests in RULE_TO_TEST.items():
        assert tests, rule
        for test_name in tests:
            assert f"def {test_name}(" in src, f"{rule} → {test_name} no existe"


def test_canonical_rule_map_documents_every_rule():
    for rule in ("LINKEDIN-RULES-002 §2", "LINKEDIN-RULES-002 §8",
                 "PromptA-v2.0+linkedin §8", "PromptA-v2.0+linkedin §5"):
        assert rule in CANONICAL_RULE_MAP
        assert len(CANONICAL_RULE_MAP[rule]) > 40


def test_match_basis_always_populated():
    """match_basis debe permitir reconstruir por qué se decidió (spec §3)."""
    cases = [
        EmployerIdentityInput(observed_employer="L'Oréal"),
        EmployerIdentityInput(observed_employer="Cartier"),
        EmployerIdentityInput(observed_employer=None),
        EmployerIdentityInput(observed_employer="Benefit Cosmetics",
                              observed_retail_channel="El Palacio de Hierro"),
    ]
    for case in cases:
        r = match_employer(case)
        assert r.match_basis, case
        assert MatchBasis.EMPLOYER_FIELD_AUTHORITATIVE in r.match_basis \
            or MatchBasis.EMPLOYER_EVIDENCE_MISSING in r.match_basis


def test_blocked_set_is_not_hardcoded_into_logic():
    """El set se inyecta; la lógica no lo muta."""
    custom = frozenset({"Marca Fantasma"})
    r = match_employer(EmployerIdentityInput(
        observed_employer="Marca Fantasma S.A.", blocked_employer_set=custom))
    assert r.match_status == MatchStatus.BLOCKED
    # Fuera del set custom, L'Oréal ya no bloquea.
    r2 = match_employer(EmployerIdentityInput(
        observed_employer="L'Oréal", blocked_employer_set=custom))
    assert r2.match_status == MatchStatus.NOT_BLOCKED


def test_no_network_access_in_matcher():
    src = (SCRIPTS / "linkedin_identity_matcher.py").read_text()
    for forbidden in ("import urllib", "import socket", "import requests",
                      "urlopen", "http.client"):
        assert forbidden not in src

def test_m07b_distinct_entity_containing_blocked_name_is_not_a_variant():
    """'ORÉAL' (sin el prefijo 'L'') es entidad DISTINTA de "L'Oréal".

    RULES §2 lista 'L\'Oréal' en el set blocked, no 'ORÉAL'. No existe regla
    canónica que las equipare, así que el matcher NO debe inferir BLOCKED.
    Este caso protege contra la tentación de ampliar el matching por substring
    para "recordar" una variante no canónica.
    """
    for name in ("ORÉAL", "oreal"):
        r = match_employer(EmployerIdentityInput(observed_employer=name))
        assert r.employer_match is False, name
        assert r.match_status in (MatchStatus.NOT_BLOCKED, MatchStatus.AMBIGUOUS), name
