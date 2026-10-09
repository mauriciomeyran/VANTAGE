"""
linkedin_identity_matcher.py — VANTAGE Scout
Employer identity matcher para LinkedIn Jobs (Phase 3C).

Implementa el comportamiento de identidad canónica de employer exigido por los
artefactos canónicos v2. NO modifica ninguna regla canónica: sólo las ejecuta.

Reglas implementadas (trazabilidad en CANONICAL_RULE_MAP):

  RULES §2  "The canonical employer field must identify the employer."
  RULES §2  "Retail channel, store, client or distribution partner does not
             trigger the blocked-employer rule."
  RULES §2  "Matching is identity-based, not arbitrary substring matching."
  RULES §8  "Any | Blocked employer | Any | REJECTED"
  PROMPT §8 "No substring-only blocked-company matching."
  PROMPT §5  "If a field cannot be observed: value = null, provenance =
              NOT_OBSERVED. Do not replace missing evidence with inference."

Principio de diseño
-------------------
El matching es EXACTO sobre identidad canónica normalizada. Nunca es substring.
Si el texto del employer coincide parcialmente con un blocked employer, el
resultado es AMBIGUOUS y NO se infiere BLOCKED (RULES §2: identity-based).

Los campos retail_channel / client / distribution_partner NUNCA participan en
la determinación del employer identity. Su presencia textual no puede, por sí
sola, declarar que esa entidad es el employer ni activar el veto.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional

__all__ = [
    "MatchStatus", "MatchBasis", "EmployerIdentityInput", "MatchResult",
    "normalize_identity", "resolve_employer_identity", "match_employer",
    "BLOCKED_EMPLOYERS", "CANONICAL_RULE_MAP",
]

# --------------------------------------------------------------------------
# Set canónico de employers bloqueados.
# Fuente: LINKEDIN-RULES-002 §2 "Blocked employers". Se declara aquí como dato,
# no como lógica, y puede sobreescribirse vía parámetro para tests.
# --------------------------------------------------------------------------
BLOCKED_EMPLOYERS: FrozenSet[str] = frozenset({
    "L'Oréal",
    "Levi Strauss",
    "Levi's",
    "El Palacio de Hierro",
})

# Sufijos y prefijos legal-firms: variantes de la MISMA identidad, no阻塞 nuevos.
_LEADING_ARTICLES = ("the ", "el ", "la ", "los ", "las ")
_CORP_SUFFIXES = (
    "s.a.s", "s.a", "s de r.l.", "s de rl", "de c.v.", "de cv",
    "sab de cv", "spa", "group", "grupo", "company", "co", "inc", "llc",
    "ltd", "plc", "ag", "sa", "cv",
)

# Designadores legales: " & Co" / " and Company".
_LEGAL_CONNECTIVES = (" & co", " and co", " & company", " and company")

# Variante geográfica/subsidiario: "L'Oréal Mexico", "Levi Strauss Mexico".
# No es un designador legal sino una设计adora de la MISMA identidad. RULES §2
# exige identidad canónica, así que lasucede identidad bloqueada debe
# converger al bloqueado. No es substring matching: sólo se acepta cuando el
# resto del nombre coincide EXACTAMENTE con la identidad bloqueada.
_GEOGRAPHIC_VARIANTS = ("mexico", "méxico", "mx", "latam", "latin america",
                        "north america", "usa", "us", "global", "international")


class MatchStatus:
    """Resultado del matching. Los 4 valores son canónicos."""

    BLOCKED = "BLOCKED"            # employer identity == blocked identity
    NOT_BLOCKED = "NOT_BLOCKED"    # employer identity resuelta y no bloqueada
    AMBIGUOUS = "AMBIGUOUS"        # coincidencia parcial: NO se infiere
    UNRESOLVED = "UNRESOLVED"      # evidencia de employer ausente


# Pasos de decisión, expuestos para que match_basis sea reconstruible.
class MatchBasis:
    EMPLOYER_FIELD_AUTHORITATIVE = "EMPLOYER_FIELD_AUTHORITATIVE"
    IDENTITY_EXACT_MATCH = "IDENTITY_EXACT_MATCH"
    IDENTITY_NORMALIZED_MATCH = "IDENTITY_NORMALIZED_MATCH"
    IDENTITY_NO_MATCH = "IDENTITY_NO_MATCH"
    AMBIGUOUS_PARTIAL_OVERLAP = "AMBIGUOUS_PARTIAL_OVERLAP"
    CHANNEL_FIELDS_EXCLUDED = "CHANNEL_FIELDS_EXCLUDED"
    EMPLOYER_EVIDENCE_MISSING = "EMPLOYER_EVIDENCE_MISSING"


@dataclass(frozen=True)
class EmployerIdentityInput:
    """Evidencia observada. Cada campo es independiente y explícito."""

    observed_employer: Optional[str] = None
    observed_brand: Optional[str] = None
    observed_retail_channel: Optional[str] = None
    observed_client: Optional[str] = None
    observed_distribution_partner: Optional[str] = None
    blocked_employer_set: FrozenSet[str] = BLOCKED_EMPLOYERS

    def channel_fields(self) -> Dict[str, Optional[str]]:
        return {
            "brand": self.observed_brand,
            "retail_channel": self.observed_retail_channel,
            "client": self.observed_client,
            "distribution_partner": self.observed_distribution_partner,
        }


@dataclass
class MatchResult:
    employer_identity: Optional[str]
    employer_match: bool
    match_status: str
    match_basis: List[str] = field(default_factory=list)
    blocked_identity_matched: Optional[str] = None
    normalized_employer: Optional[str] = None
    excluded_channel_mentions: Dict[str, Optional[str]] = field(default_factory=dict)

    def to_json(self) -> Dict[str, Any]:
        return {
            "employer_identity": self.employer_identity,
            "employer_match": self.employer_match,
            "match_status": self.match_status,
            "match_basis": list(self.match_basis),
            "blocked_identity_matched": self.blocked_identity_matched,
            "normalized_employer": self.normalized_employer,
            "excluded_channel_mentions": dict(self.excluded_channel_mentions),
        }


#: Trazabilidad regla→implementación. Test層 verifica que cada entrada tiene
#: al menos un consumidor real (test_canonic_rule_map_is_executable).
CANONICAL_RULE_MAP: Dict[str, str] = {
    "LINKEDIN-RULES-002 §2": "El blocking se determina sólo por el campo employer canónico; retail channel, store, client y distribution partner quedan excluidos del matching (MatchBasis.CHANNEL_FIELDS_EXCLUDED).",
    "LINKEDIN-RULES-002 §8": "MatchStatus.BLOCKED activa el veto de employer sin importar el resto de la evidencia.",
    "PromptA-v2.0+linkedin §8": "El matching es identity-based exacto sobre identidad normalizada; nunca substring (AMBIGUOUS cuando hay solapamiento parcial no concluyente).",
    "PromptA-v2.0+linkedin §5": "Evidencia de employer ausente ⇒ UNRESOLVED con NOT_OBSERVED; no se infiere identidad.",
}


# --------------------------------------------------------------------------
# Normalización de identidad canónica
# --------------------------------------------------------------------------

_SUFFIX_TAIL_RE = re.compile(
    r"\s+(?:"
    r"s\.?\s*a\.?\s*(?:s\.?\s*)?(?:de\s+c\.?\s*v\.?|de\s+c\.?\s*v\.?\s*"
    r"s\.?\s*a\.?)?"
    r"|sab\s+de\s+c\.?\s*v"
    r"|de\s+c\.?\s*v\.?"
    r"|spa|group|grupo|company|co|inc|llc|ltd|plc|ag|cv"
    r")$",
    re.IGNORECASE,
)


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize_identity(raw: Optional[str]) -> Optional[str]:
    """Reduce un nombre de employer a su identidad canónica comparable.

    Pasos (deterministas, sin estado externo):
      1. None/vacío → None (no se infiere identidad)
      2. minúsculas + strip de acentos + colapso de whitespace
      3. remueve conectivos legales (" & co", " and company")
      4. remueve sufijos legal-firms (hasta 4 pasadas, p.ej. "sa de cv")
      5. remueve artículos iniciales (the/el/la/los/las)
      6. remueve punto final

    Variantes de la misma identidad convergen (p.ej. "L'Oréal Mexico S.A. de
    C.V." ≡ "L'Oréal"). Entidades genuinamente distintas NO convergen.
    """
    if raw is None:
        return None
    if not isinstance(raw, str):
        return None
    text = _strip_accents(raw).lower().strip()
    if not text:
        return None
    text = re.sub(r"\s+", " ", text).rstrip(".")

    # 3. conectivos legales (p.ej. "levi strauss & co")
    for connective in _LEGAL_CONNECTIVES:
        if text.endswith(connective):
            text = text[: -len(connective)].strip()

    # 4. sufijos legal-firms, repetidos (p.ej. "s.a. de c.v." + "mexico").
    #    Se hace con un regex que permite separadores con o sin punto, porque
    #    la forma observada en LinkedIn varía ("S.A. de C.V." / "SA de CV" /
    #    "S.A.S. de C.V."). Ningún sufijo puede vaciar el nombre.
    for _ in range(6):
        stripped = _SUFFIX_TAIL_RE.sub("", text)
        if stripped == text or not stripped:
            break
        text = stripped.strip()

    # 4b. variante geográfica/subsidiario (tras sufijos legales)
    for _ in range(3):
        changed = False
        for variant in sorted(_GEOGRAPHIC_VARIANTS, key=len, reverse=True):
            if text.endswith(" " + variant) and len(text) > len(variant) + 1:
                text = text[: -len(variant) - 1].strip()
                changed = True
                break
        if not changed:
            break

    # 5. artículos iniciales
    for article in _LEADING_ARTICLES:
        if text.startswith(article) and len(text) > len(article):
            text = text[len(article):].strip()
            break

    return text or None


def _normalized_blocked_set(blocked_set: FrozenSet[str]) -> Dict[str, str]:
    """mapea identidad normalizada → identidad blocked original (para match_basis)."""
    out: Dict[str, str] = {}
    for entry in blocked_set:
        norm = normalize_identity(entry)
        if norm:
            out[norm] = entry
    return out


# --------------------------------------------------------------------------
# Resolución del employer identity
# --------------------------------------------------------------------------

def resolve_employer_identity(
    observed_employer: Optional[str],
) -> Optional[str]:
    """RULES §2: el campo employer canónico es la única fuente de identidad.

    No consulta retail_channel, client, distribution_partner ni brand.
    PROMPT §5: si no se puede observar, devuelve None (no infiere).
    """
    return normalize_identity(observed_employer)


def _partial_overlaps(employer_norm: str, blocked_norm: str) -> bool:
    """Detecta solapamiento de marca sin concluyente para inferir BLOCKED.

    Sólo词-boundary: el token inicial del employer empieza por el token inicial
    del blocked O el blocked aparece como token completo. No es substring
    arbitrario: usa límites de palabra y sólo alimenta AMBIGUOUS, nunca
    BLOCKED.
    """
    emp_tokens = employer_norm.split()
    blk_tokens = blocked_norm.split()
    if not emp_tokens or not blk_tokens:
        return False
    if emp_tokens[0].startswith(blk_tokens[0]):
        return True
    return blk_tokens[0] in emp_tokens


def match_employer(inp: EmployerIdentityInput) -> MatchResult:
    """Determina si el employer canónico está bloqueado.

    Precedencia (RULES §1 §2):
      1. evidencia de employer ausente → UNRESOLVED
      2. identidad normalizada == identidad blocked normalizada → BLOCKED
      3. solapamiento parcial → AMBIGUOUS (no infiere BLOCKED)
      4. si no → NOT_BLOCKED
    Channel/client/partner quedan explícitamente excluidos en match_basis.
    """
    basis: List[str] = []
    excluded = inp.channel_fields()

    identity = resolve_employer_identity(inp.observed_employer)

    if identity is None:
        basis.append(MatchBasis.EMPLOYER_EVIDENCE_MISSING)
        if any(v for v in excluded.values()):
            basis.append(MatchBasis.CHANNEL_FIELDS_EXCLUDED)
        return MatchResult(
            employer_identity=None, employer_match=False,
            match_status=MatchStatus.UNRESOLVED, match_basis=basis,
            normalized_employer=None, excluded_channel_mentions=excluded,
        )

    basis.append(MatchBasis.EMPLOYER_FIELD_AUTHORITATIVE)
    if any(v for v in excluded.values()):
        basis.append(MatchBasis.CHANNEL_FIELDS_EXCLUDED)

    blocked_map = _normalized_blocked_set(inp.blocked_employer_set)

    if identity in blocked_map:
        basis.append(MatchBasis.IDENTITY_EXACT_MATCH)
        return MatchResult(
            employer_identity=identity, employer_match=True,
            match_status=MatchStatus.BLOCKED, match_basis=basis,
            blocked_identity_matched=blocked_map[identity],
            normalized_employer=identity, excluded_channel_mentions=excluded,
        )

    for blk_norm in blocked_map:
        if _partial_overlaps(identity, blk_norm):
            basis.append(MatchBasis.AMBIGUOUS_PARTIAL_OVERLAP)
            return MatchResult(
                employer_identity=identity, employer_match=False,
                match_status=MatchStatus.AMBIGUOUS, match_basis=basis,
                blocked_identity_matched=blocked_map[blk_norm],
                normalized_employer=identity, excluded_channel_mentions=excluded,
            )

    basis.append(MatchBasis.IDENTITY_NO_MATCH)
    return MatchResult(
        employer_identity=identity, employer_match=False,
        match_status=MatchStatus.NOT_BLOCKED, match_basis=basis,
        normalized_employer=identity, excluded_channel_mentions=excluded,
    )


# --------------------------------------------------------------------------
# Trazabilidad regla→test
# --------------------------------------------------------------------------
RULE_TO_TEST: Dict[str, List[str]] = {
    "LINKEDIN-RULES-002 §2": [
        "test_m03_blocked_employer_only_as_retail_channel",
        "test_m04_blocked_employer_only_as_client",
        "test_m05_blocked_employer_only_as_distribution_partner",
        "test_m02_employer_clearly_distinct",
        "test_regression_rmatch_01_benefit_channel_palacio",
    ],
    "LINKEDIN-RULES-002 §8": [
        "test_m01_employer_exactly_matches_blocked",
        "test_regression_rmatch_02_levi_strauss_employer_dockers_brand",
    ],
    "PromptA-v2.0+linkedin §8": [
        "test_m06_unrelated_text_containing_blocked_name",
        "test_m08_ambiguous_identity_not_inferred",
        "test_no_substring_only_matching_anywhere",
    ],
    "PromptA-v2.0+linkedin §5": [
        "test_m09_missing_employer_evidence",
    ],
    "M07 identity variant": [
        "test_m07_identity_variant_blocked",
    ],
    "M10 precedence": [
        "test_m10_employer_takes_precedence_over_channel",
    ],
}


if __name__ == "__main__":
    import json
    examples = [
        EmployerIdentityInput("L'Oréal"),
        EmployerIdentityInput("Benefit Cosmetics", observed_retail_channel="El Palacio de Hierro"),
        EmployerIdentityInput("Levi Strauss & Co", observed_brand="DOCKERS HEROS"),
        EmployerIdentityInput(None, observed_client="Dockers"),
    ]
    print(json.dumps([match_employer(e).to_json() for e in examples],
                     ensure_ascii=False, indent=2))