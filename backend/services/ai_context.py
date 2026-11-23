"""Context retrieval for the SkillPulse Intelligence Assistant.

Decides which existing SkillPulse analytics are relevant to a question
(and to earlier turns for follow-ups), loads them by calling the EXISTING
service functions, labels each block with its provenance, and renders a
size-limited text context for the LLM. No statistics are hard-coded here.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Sequence

import pandas as pd

from services.compact_market_data import (
    load_compact_market_data_report,
    load_compact_market_indicators,
)
from services.intelligence_engine import build_market_intelligence_overview
from services.official_data import (
    load_ncs_qualification_vacancies,
    load_ncs_sector_vacancies,
    load_ncs_summary,
    load_plfs_industry_distribution,
    load_plfs_monthly_cws_wpr,
    load_plfs_state_wpr,
)
from services.sector_demand_engine import (
    build_sector_demand_summary,
    load_sector_demand_trends,
)
from services.skill_gap import (
    identify_shortages,
    identify_surpluses,
    industry_wise_analysis,
    state_wise_analysis,
)

logger = logging.getLogger("skillpulse.ai.context")

CACHE_TTL_SECONDS = 300
MAX_BLOCKS = 8
MAX_BLOCK_CHARS = 7000
MAX_TOTAL_CHARS = 32000

# ---------------------------------------------------------------------------
# Provenance labels (shown to the LLM and returned to the UI as `type`)
# ---------------------------------------------------------------------------

KIND_DESCRIPTIONS = {
    "official_plfs": (
        "OFFICIAL OBSERVATION - PLFS (Periodic Labour Force Survey)"
    ),
    "official_ncs": (
        "OFFICIAL OBSERVATION - National Career Service (NCS) portal "
        "vacancies. Covers vacancies listed on the NCS platform only and "
        "is NOT the entire Indian labour market"
    ),
    "calculated": (
        "CALCULATED INDICATOR - derived by SkillPulse from official data "
        "(descriptive; not an official statistic)"
    ),
    "forecast": (
        "STATISTICAL FORECAST - exploratory model output, not an official "
        "projection"
    ),
    "illustrative": (
        "ILLUSTRATIVE SAMPLE DATA - NOT official and NOT a national "
        "skill-gap estimate"
    ),
    "mixed": (
        "MIXED - consolidated or normalised view that may combine official "
        "observations, calculated indicators and forecasts; follow any "
        "labels, units and scope fields inside the data itself"
    ),
}


@dataclass(frozen=True)
class BlockSpec:
    key: str
    title: str
    kind: str
    endpoint: str
    loader: Callable[[], Any]
    note: str = ""


def _load_forecast() -> Any:
    # Lazy import: the forecast module is optional in this project.
    from ml.plfs_forecasting import build_plfs_wpr_forecast

    return build_plfs_wpr_forecast(horizon=3)


_SPEC_LIST: list[BlockSpec] = [
    BlockSpec(
        "plfs_state",
        "PLFS state-wise worker population ratio (WPR)",
        "official_plfs",
        "/api/official/plfs/state-wpr",
        load_plfs_state_wpr,
    ),
    BlockSpec(
        "plfs_industry",
        "PLFS industry distribution of employment",
        "official_plfs",
        "/api/official/plfs/industry-distribution",
        load_plfs_industry_distribution,
    ),
    BlockSpec(
        "plfs_monthly",
        "PLFS monthly current weekly status (CWS) WPR",
        "official_plfs",
        "/api/official/plfs/monthly-cws-wpr",
        load_plfs_monthly_cws_wpr,
    ),
    BlockSpec(
        "ncs_summary",
        "NCS vacancy summary",
        "official_ncs",
        "/api/official/ncs/summary",
        load_ncs_summary,
    ),
    BlockSpec(
        "ncs_sector",
        "NCS sector-wise vacancies",
        "official_ncs",
        "/api/official/ncs/sector-vacancies",
        load_ncs_sector_vacancies,
    ),
    BlockSpec(
        "ncs_qualification",
        "NCS qualification-wise vacancies",
        "official_ncs",
        "/api/official/ncs/qualification-vacancies",
        load_ncs_qualification_vacancies,
    ),
    BlockSpec(
        "sector_trends",
        "NCS sector demand trends (two-financial-year comparison)",
        "calculated",
        "/api/analytics/sector-demand-trends",
        load_sector_demand_trends,
    ),
    BlockSpec(
        "sector_trends_summary",
        "NCS sector demand trend summary",
        "calculated",
        "/api/analytics/sector-demand-trends/summary",
        build_sector_demand_summary,
    ),
    BlockSpec(
        "forecast",
        "PLFS WPR statistical forecast",
        "forecast",
        "/api/official/plfs/wpr-forecast",
        _load_forecast,
        note=(
            "Check which geography and series this forecast covers. If it "
            "has no state-level breakdown, say that state-level forecasts "
            "are not available."
        ),
    ),
    BlockSpec(
        "market_indicators",
        "Normalised market indicators",
        "mixed",
        "/api/analytics/market-indicators",
        lambda: load_compact_market_indicators(
            dataset="", indicator="", category_type="", category="", limit=1000
        ),
    ),
    BlockSpec(
        "market_indicators_report",
        "Market indicator data-quality report",
        "mixed",
        "/api/analytics/market-indicators/summary",
        load_compact_market_data_report,
    ),
    BlockSpec(
        "overview",
        "Integrated market intelligence overview",
        "mixed",
        "/api/intelligence/overview",
        lambda: build_market_intelligence_overview(horizon=1),
    ),
    BlockSpec(
        "skill_gap_states",
        "Legacy sample skill-gap analysis by state",
        "illustrative",
        "/api/states",
        state_wise_analysis,
        note="Rows come from a small illustrative sample file.",
    ),
    BlockSpec(
        "skill_gap_industries",
        "Legacy sample skill-gap analysis by industry",
        "illustrative",
        "/api/industries",
        industry_wise_analysis,
        note="Rows come from a small illustrative sample file.",
    ),
    BlockSpec(
        "skill_gap_shortages",
        "Legacy sample skill shortages",
        "illustrative",
        "/api/shortages",
        identify_shortages,
        note="Rows come from a small illustrative sample file.",
    ),
    BlockSpec(
        "skill_gap_surpluses",
        "Legacy sample skill surpluses",
        "illustrative",
        "/api/surpluses",
        identify_surpluses,
        note="Rows come from a small illustrative sample file.",
    ),
]
SPEC_BY_KEY = {spec.key: spec for spec in _SPEC_LIST}

TOPIC_BLOCKS: dict[str, list[str]] = {
    "forecast": ["forecast"],
    "plfs_state": ["plfs_state"],
    "ncs_sector": [
        "ncs_summary",
        "ncs_sector",
        "sector_trends",
        "sector_trends_summary",
    ],
    "plfs_industry": ["plfs_industry"],
    "ncs_qualification": ["ncs_summary", "ncs_qualification"],
    "plfs_monthly": ["plfs_monthly"],
    "indicators": ["market_indicators", "market_indicators_report"],
    "skill_gap": [
        "skill_gap_states",
        "skill_gap_industries",
        "skill_gap_shortages",
        "skill_gap_surpluses",
    ],
    "overview": ["overview"],
}

# Order matters: earlier topics get their blocks into the budget first.
_TOPIC_RULES: list[tuple[str, re.Pattern[str]]] = [
    (name, re.compile(pattern, re.IGNORECASE))
    for name, pattern in (
        (
            "forecast",
            r"forecast|predict|projection|future|outlook|expected|"
            r"next (month|quarter|year)|coming (months|year)",
        ),
        (
            "plfs_state",
            r"employ|unemploy|\bwpr\b|worker|workforce|labou?r|"
            r"participation|plfs|\bjobs?\b|\bstates?\b",
        ),
        (
            "ncs_sector",
            r"vacanc|\bncs\b|hiring|job (market|opening|posting)|sector|"
            r"industr|demand|growing|increasing",
        ),
        (
            "plfs_industry",
            r"industry distribution|employment by (sector|industry)|"
            r"agricultur|manufactur|construction|services sector|"
            r"primary|secondary|tertiary|sector.wise employment",
        ),
        (
            "ncs_qualification",
            r"qualification|education|degree|graduate|diploma|\biti\b|"
            r"postgraduate",
        ),
        (
            "plfs_monthly",
            r"month|cws|current weekly|historical|history|past|over time|"
            r"trend",
        ),
        ("indicators", r"indicator|statistic|data quality|dataset"),
        ("skill_gap", r"skill|shortage|surplus|\bgaps?\b|upskill|reskill|training"),
        (
            "overview",
            r"overview|overall|summary|situation|challenge|polic|priorit|"
            r"recommend|strateg",
        ),
    )
]

_NATIONAL_RE = re.compile(
    r"\b(india as a whole|all of india|all india|nationwide|national|"
    r"nationally|across india|whole country|entire country|all states|"
    r"every state|states)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ContextBlock:
    spec: BlockSpec
    payload: Any = None
    rows_total: int | None = None
    note: str = ""
    error: str | None = None
    timestamp: str | None = None


@dataclass
class ChatContext:
    text: str
    sources: list[dict[str, Any]]
    states: list[str]
    topics: list[str]
    data_timestamp: str | None
    retrieved_at: str


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

_CACHE: dict[str, tuple[float, Any]] = {}


def _load_cached(spec: BlockSpec) -> Any:
    now = time.monotonic()
    hit = _CACHE.get(spec.key)
    if hit and now - hit[0] < CACHE_TTL_SECONDS:
        return hit[1]
    value = spec.loader()
    _CACHE[spec.key] = (now, value)
    return value


def _norm(text: Any) -> str:
    value = str(text).lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def _find_column(df: pd.DataFrame, needles: Sequence[str]) -> Any:
    for col in df.columns:
        name = str(col).lower()
        if any(needle in name for needle in needles):
            return col
    return None


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    return json.loads(df.to_json(orient="records"))


def _json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:  # noqa: BLE001
            pass
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _dump(value: Any) -> str:
    return json.dumps(
        value, default=_json_default, ensure_ascii=False, separators=(",", ":")
    )


def _truncate_lists(value: Any, limit: int) -> Any:
    if isinstance(value, list):
        if len(value) > limit:
            tail = limit // 2
            value = value[: limit - tail] + value[-tail:]
        return [_truncate_lists(item, limit) for item in value]
    if isinstance(value, dict):
        return {k: _truncate_lists(v, limit) for k, v in value.items()}
    return value


def _compact(payload: Any, max_chars: int) -> tuple[str, bool]:
    text = _dump(payload)
    if len(text) <= max_chars:
        return text, False
    for limit in (60, 40, 24, 12, 8):
        text = _dump(_truncate_lists(payload, limit))
        if len(text) <= max_chars:
            return text, True
    return text[:max_chars] + "...[truncated]", True


_TIMESTAMP_KEYS = (
    "generated_at",
    "created_at",
    "last_updated",
    "updated_at",
    "timestamp",
    "generated_on",
    "run_at",
    "data_timestamp",
)


def _find_timestamp(payload: Any) -> str | None:
    if isinstance(payload, dict):
        for key in _TIMESTAMP_KEYS:
            value = payload.get(key)
            if isinstance(value, (str, int, float)) and value != "":
                return str(value)
    return None


# ---------------------------------------------------------------------------
# State and topic resolution (supports follow-up questions)
# ---------------------------------------------------------------------------


def _known_states() -> list[str]:
    """State names found in the PLFS state table, longest first."""
    try:
        df = _load_cached(SPEC_BY_KEY["plfs_state"])
    except Exception:  # noqa: BLE001
        return []
    col = _find_column(df, ("state",))
    if col is None:
        return []
    names = {str(v).strip() for v in df[col].dropna().unique()}
    skip = {"all india", "india", "all-india", ""}
    return sorted((n for n in names if n.lower() not in skip), key=len, reverse=True)


def _match_states(text: str, known: Sequence[str]) -> list[str]:
    haystack = f" {_norm(text)} "
    accepted: list[str] = []
    hits: list[tuple[int, str]] = []
    for name in known:  # longest first
        norm_name = _norm(name)
        if not norm_name or any(norm_name in other for other in accepted):
            continue
        pos = haystack.find(f" {norm_name} ")
        if pos >= 0:
            accepted.append(norm_name)
            hits.append((pos, name))
    hits.sort()
    return [name for _, name in hits][:3]


def _resolve_states(
    question: str, history: Sequence[tuple[str, str]], known: Sequence[str]
) -> list[str]:
    direct = _match_states(question, known)
    if direct:
        return direct
    if _NATIONAL_RE.search(question):
        return []
    for role, content in reversed(history):
        if role == "user":
            found = _match_states(content, known)
            if found:
                return found
    return []


def _detect_topics(text: str) -> list[str]:
    return [name for name, rx in _TOPIC_RULES if rx.search(text)]


def _resolve_topics(
    question: str, history: Sequence[tuple[str, str]], states: Sequence[str]
) -> list[str]:
    topics = _detect_topics(question)
    if not topics:  # follow-up like "tell me more"
        for role, content in reversed(history):
            if role == "user":
                topics = _detect_topics(content)
                if topics:
                    break
    if states:
        for extra in ("plfs_state", "indicators"):
            if extra not in topics:
                topics.append(extra)
        if set(topics) <= {"plfs_state", "indicators", "overview"}:
            for extra in ("plfs_industry", "ncs_sector"):
                if extra not in topics:
                    topics.append(extra)
    if not topics:
        topics = ["overview", "plfs_state"]
    return topics


def _select_specs(topics: Sequence[str]) -> list[BlockSpec]:
    keys: list[str] = []
    for topic in topics:
        for key in TOPIC_BLOCKS.get(topic, []):
            if key not in keys:
                keys.append(key)
    return [SPEC_BY_KEY[k] for k in keys[:MAX_BLOCKS]]


# ---------------------------------------------------------------------------
# Block building and rendering
# ---------------------------------------------------------------------------


def _match_rows(df: pd.DataFrame, states: Sequence[str]) -> pd.DataFrame | None:
    wanted = {_norm(s) for s in states}
    mask = pd.Series(False, index=df.index)
    for i in range(df.shape[1]):
        series = df.iloc[:, i]
        if pd.api.types.is_numeric_dtype(series):
            continue
        mask |= series.astype(str).map(_norm).isin(wanted)
    return df[mask] if bool(mask.any()) else None


def _shape(raw: Any, states: Sequence[str]) -> tuple[Any, int | None, str]:
    if isinstance(raw, pd.DataFrame):
        records = _records(raw)
        total = len(raw)
        if not states:
            return records, total, ""
        matched = _match_rows(raw, states)
        if matched is None:
            return (
                records,
                total,
                "No state-level breakdown was found in this dataset; it is "
                "shown as provided.",
            )
        return (
            {
                "rows_for_requested_state": _records(matched),
                "all_rows_for_comparison": records,
            },
            total,
            f"{len(matched)} row(s) matched the requested state(s).",
        )
    return raw, None, ""


async def _build_block(spec: BlockSpec, states: Sequence[str]) -> ContextBlock:
    try:
        raw = await asyncio.to_thread(_load_cached, spec)
        payload, total, shape_note = _shape(raw, states)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Context block %s unavailable: %r", spec.key, exc)
        return ContextBlock(spec=spec, error=type(exc).__name__)
    note = " ".join(part for part in (spec.note, shape_note) if part)
    return ContextBlock(
        spec=spec,
        payload=payload,
        rows_total=total,
        note=note,
        timestamp=_find_timestamp(raw),
    )


def _render_block(index: int, block: ContextBlock, limit: int) -> tuple[str, bool]:
    spec = block.spec
    lines = [
        f"=== DATA BLOCK {index}: {spec.title} ===",
        f"Endpoint: {spec.endpoint}",
        f"Data type: {KIND_DESCRIPTIONS[spec.kind]}",
    ]
    if block.error:
        lines.append(
            "Status: UNAVAILABLE - this data could not be retrieved. Say so "
            "instead of guessing."
        )
        return "\n".join(lines), False
    if block.note:
        lines.append(f"Note: {block.note}")
    if block.rows_total is not None:
        lines.append(f"Rows in full dataset: {block.rows_total}")
    text, truncated = _compact(block.payload, limit)
    if truncated:
        lines.append(
            "Note: payload was shortened to fit; long lists keep their first "
            "and last rows."
        )
    lines.append("Data (JSON):")
    lines.append(text)
    return "\n".join(lines), truncated


async def build_chat_context(
    question: str, history: Sequence[tuple[str, str]]
) -> ChatContext:
    known = await asyncio.to_thread(_known_states)
    states = _resolve_states(question, history, known)
    topics = _resolve_topics(question, history, states)
    specs = _select_specs(topics)
    blocks = await asyncio.gather(*(_build_block(s, states) for s in specs))

    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    parts = [
        f"Retrieved at (UTC): {retrieved_at}",
        "Focus state(s) detected: "
        + (", ".join(states) if states else "none (national / all-states view)"),
        "Topics detected: " + ", ".join(topics),
    ]
    sources: list[dict[str, Any]] = []
    remaining = MAX_TOTAL_CHARS
    data_timestamp: str | None = None

    for index, block in enumerate(blocks, start=1):
        spec = block.spec
        status = "ok"
        if block.error:
            parts.append(_render_block(index, block, 0)[0])
            status = "unavailable"
        elif remaining < 1500:
            status = "omitted"
        else:
            text, truncated = _render_block(
                index, block, min(MAX_BLOCK_CHARS, remaining)
            )
            parts.append(text)
            remaining -= len(text)
            if truncated:
                status = "truncated"
            if data_timestamp is None and block.timestamp:
                data_timestamp = block.timestamp
        sources.append(
            {
                "name": spec.title,
                "type": spec.kind,
                "endpoint": spec.endpoint,
                "status": status,
            }
        )

    return ChatContext(
        text="\n\n".join(parts),
        sources=[s for s in sources if s["status"] != "omitted"],
        states=states,
        topics=topics,
        data_timestamp=data_timestamp,
        retrieved_at=retrieved_at,
    )