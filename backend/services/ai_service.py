"""
SkillPulse AI - Local Intelligence Engine
No OpenAI API or paid LLM required.
"""

import re
import json
import logging
import math
from typing import Any

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
SkillPulse AI is an Indian Labour Market Intelligence platform.

It analyses:
- PLFS employment indicators
- NCS vacancies
- State-wise employment
- Sector-wise demand
- Employment forecasts
- Skill development opportunities
"""


class AIServiceError(Exception):

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def llm_status():

    return {
        "configured": True,
        "provider": "skillpulse-local",
        "model": "SkillPulse Intelligence Engine"
    }


def extract_data(context):

    blocks = []

    pattern = (
        r"=== DATA BLOCK \d+: (.*?) ==="
        r".*?Data \(JSON\):\n"
        r"(.*?)(?=\n\n=== DATA BLOCK|\Z)"
    )

    matches = re.findall(pattern, context, re.DOTALL)

    for title, raw_data in matches:

        try:
            data = json.loads(raw_data.strip())

            blocks.append({
                "title": title,
                "data": data
            })

        except json.JSONDecodeError:
            continue

    return blocks


def flatten_data(data):

    if isinstance(data, list):
        return data

    if isinstance(data, dict):

        if "rows_for_requested_state" in data:
            return data["rows_for_requested_state"]

        if "all_rows_for_comparison" in data:
            return data["all_rows_for_comparison"]

        return [data]

    return []


def detect_intent(question):

    q = question.lower()

    if "state analysis" in q or (
        ("state-level plfs" in q or "state-specific plfs" in q)
        and "ncs" in q
    ):
        return "state_analysis"

    if any(x in q for x in [
        "forecast", "future", "predict",
        "prediction", "upcoming", "2030"
    ]):
        return "forecast"

    if any(x in q for x in [
        "skill gap", "shortage", "skills needed",
        "training", "improve skills"
    ]):
        return "skills"

    if any(x in q for x in [
        "vacancy", "vacancies", "hiring",
        "job demand", "sector demand"
    ]):
        return "demand"

    if any(x in q for x in [
        "employment", "employed",
        "unemployment", "wpr", "workers"
    ]):
        return "employment"

    if any(x in q for x in [
        "compare", "comparison", "difference"
    ]):
        return "comparison"

    return "overview"


def format_record(record):

    if not isinstance(record, dict):
        return str(record)

    ignored = {
        "source_url",
        "source_document",
        "source_report"
    }

    values = []

    for key, value in record.items():

        if key in ignored:
            continue

        if value is None:
            continue

        label = key.replace("_", " ").title()

        values.append(f"{label}: {value}")

        if len(values) >= 7:
            break

    return "\n".join(values)


def _finite_float(value: Any) -> float | None:
    try:
        amount = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return amount if math.isfinite(amount) else None


def _forecast_points(value: Any, field: str) -> list[tuple[str, float]]:
    if not isinstance(value, list):
        return []

    points = []
    for row in value:
        if not isinstance(row, dict):
            continue

        amount = _finite_float(row.get(field))
        if amount is None:
            continue

        period = str(row.get("reference_month") or "unknown period")
        points.append((period, amount))

    return points


def _format_wpr(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _summarize_wpr_change(
    label: str,
    start_period: str,
    start_value: float,
    end_period: str,
    end_value: float,
) -> str:
    change = end_value - start_value
    if abs(change) < 0.0005:
        movement = (
            "remained unchanged at the reported precision "
            f"(change {change:+.3f} percentage points)"
        )
    elif change > 0:
        movement = f"increased by {change:.3f} percentage points"
    else:
        movement = f"decreased by {abs(change):.3f} percentage points"

    return (
        f"{label} {movement}, from {_format_wpr(start_value)}% in "
        f"{start_period} to {_format_wpr(end_value)}% in {end_period}."
    )


def generate_forecast_interpretation(forecast: Any) -> str:
    if not isinstance(forecast, dict):
        return "Forecast interpretation is unavailable because the forecast data is invalid."

    baseline = _forecast_points(forecast.get("forecast"), "forecast_wpr_pct")
    if not baseline:
        return (
            "Forecast interpretation is unavailable because there are no valid "
            "predicted WPR values."
        )

    history = _forecast_points(forecast.get("history"), "actual_wpr_pct")
    trend = _forecast_points(forecast.get("trend_forecast"), "forecast_wpr_pct")
    start = history[-1] if history else None

    answer = [
        "SKILLPULSE AI FORECAST INTERPRETATION",
        "",
        "FUTURE OUTLOOK",
    ]

    if start:
        answer.append(
            _summarize_wpr_change(
                "The selected-model baseline",
                start[0],
                start[1],
                baseline[-1][0],
                baseline[-1][1],
            )
        )
    else:
        answer.append(
            f"The selected-model baseline forecasts "
            f"{_format_wpr(baseline[-1][1])}% for {baseline[-1][0]}."
        )

    if trend:
        trend_start = start or (trend[0] if len(trend) > 1 else None)
        if trend_start:
            answer.append(
                _summarize_wpr_change(
                    "The separate dynamic trend scenario",
                    trend_start[0],
                    trend_start[1],
                    trend[-1][0],
                    trend[-1][1],
                )
            )
        else:
            answer.append(
                f"The dynamic trend scenario forecasts "
                f"{_format_wpr(trend[-1][1])}% for {trend[-1][0]}."
            )

        if baseline[-1][0] == trend[-1][0]:
            difference = trend[-1][1] - baseline[-1][1]
            answer.append(
                f"At {baseline[-1][0]}, the trend scenario is "
                f"{abs(difference):.3f} percentage points "
                f"{'above' if difference >= 0 else 'below'} the baseline."
            )

    selected_model = str(
        forecast.get("selected_model")
        or forecast.get("best_validated_model")
        or "the selected model"
    )
    validation = forecast.get("validation")
    metrics = (
        validation.get("model_comparison", [])
        if isinstance(validation, dict)
        else []
    )
    selected_metrics = next(
        (
            metric
            for metric in metrics
            if isinstance(metric, dict) and metric.get("model") == selected_model
        ),
        None,
    )

    answer.extend(["", "MODEL RELIABILITY"])
    if selected_metrics:
        answer.append(
            f"The selected baseline model is {selected_model}. Its rolling-origin "
            f"backtest errors are MAE {selected_metrics.get('mae', 'unavailable')} "
            f"and RMSE {selected_metrics.get('rmse', 'unavailable')} WPR "
            f"percentage points, with sMAPE "
            f"{selected_metrics.get('smape_pct', 'unavailable')}%. Lower errors "
            "are better; these historical errors are not confidence intervals."
        )
    else:
        answer.append(
            f"The selected baseline model is {selected_model}, but matching "
            "validation metrics are unavailable."
        )

    trend_model = str(forecast.get("trend_model") or "")
    trend_metrics = next(
        (
            metric
            for metric in metrics
            if isinstance(metric, dict) and metric.get("model") == trend_model
        ),
        None,
    )
    trend_mae = (
        _finite_float(trend_metrics.get("mae"))
        if trend_metrics
        else None
    )
    if trend and trend_mae is not None:
        scenario_gap = abs(trend[-1][1] - baseline[-1][1])
        if scenario_gap < trend_mae:
            answer.append(
                f"The {scenario_gap:.3f}-percentage-point gap between the "
                f"baseline and trend scenarios is smaller than the trend model's "
                f"historical MAE ({trend_mae:.4f} percentage points). Treat it "
                "as an alternative scenario, not reliable evidence of an improvement."
            )

    answer.extend(
        [
            "",
            "SCOPE AND LIMITATIONS",
            f"This forecast covers {forecast.get('population_scope', 'the population scope is unspecified')}. "
            "WPR is an employment-to-population indicator, not an unemployment "
            "rate, and this forecast does not directly predict job counts, "
            "vacancies, or skill gaps. It is an exploratory short-term model "
            "output, not an official projection.",
        ]
    )

    warning = forecast.get("methodology_warning")
    if warning:
        answer.append(f"Methodology note: {warning}")

    return "\n".join(answer)


def generate_state_analysis(blocks: list[dict[str, Any]]) -> str:
    state_block = next(
        (block for block in blocks if "plfs state-wise" in block["title"].lower()),
        None,
    )
    state_rows = flatten_data(state_block["data"]) if state_block else []
    state_record = next(
        (row for row in state_rows if isinstance(row, dict)),
        None,
    )

    answer = ["SKILLPULSE STATE ANALYSIS", "", "STATE EMPLOYMENT SNAPSHOT"]
    if state_record:
        state_name = state_record.get("state_ut", "Selected state")
        survey_period = state_record.get("survey_period", "not reported")
        answer.append(f"PLFS survey period: {survey_period}.")

        measures = (
            ("combined WPR", "rural_urban_person_wpr_pct"),
            ("rural WPR", "rural_person_wpr_pct"),
            ("urban WPR", "urban_person_wpr_pct"),
            ("male WPR", "rural_urban_male_wpr_pct"),
            ("female WPR", "rural_urban_female_wpr_pct"),
        )
        reported = [
            f"{label} {_finite_float(state_record.get(key)):.1f}%"
            for label, key in measures
            if _finite_float(state_record.get(key)) is not None
        ]
        if reported:
            answer.append(f"{state_name}: " + "; ".join(reported) + ".")
        else:
            answer.append(f"No WPR values were reported for {state_name}.")
    else:
        answer.append("No state-specific PLFS WPR record was available.")

    ncs_block = next(
        (
            block
            for block in blocks
            if "ncs sector-wise vacancies" in block["title"].lower()
        ),
        None,
    )
    ncs_rows = flatten_data(ncs_block["data"]) if ncs_block else []
    ncs_rows = [row for row in ncs_rows if isinstance(row, dict)]
    ncs_rows.sort(
        key=lambda row: _finite_float(row.get("vacancies_fy2023_24"))
        if _finite_float(row.get("vacancies_fy2023_24")) is not None
        else -1,
        reverse=True,
    )

    answer.extend(
        [
            "",
            "NATIONAL NCS SECTOR SIGNALS",
            "These are vacancies reported on the national NCS platform, not "
            "state-level vacancy counts.",
        ]
    )
    if ncs_rows:
        for row in ncs_rows[:3]:
            sector = row.get("ncs_sector_as_published", "Unspecified sector")
            current = _finite_float(row.get("vacancies_fy2023_24"))
            previous = _finite_float(row.get("vacancies_fy2022_23"))
            change = _finite_float(row.get("reported_percent_change"))
            line = f"{sector}: "
            if current is None:
                line += "FY 2023-24 vacancy count not reported."
            else:
                line += f"{current:,.0f} vacancies in FY 2023-24"
                if previous is not None:
                    line += f", versus {previous:,.0f} in FY 2022-23"
                if change is not None:
                    line += f" ({change:+.1f}% reported change)"
                line += "."
            answer.append(line)
    else:
        answer.append("NCS sector vacancy data was unavailable.")

    answer.extend(
        [
            "",
            "INTERPRETATION AND LIMITATIONS",
            "WPR is an employment-to-population indicator, not an unemployment "
            "rate. National NCS vacancy changes can provide context, but they "
            "do not establish local vacancies, worker supply, skill gaps, or "
            "state-specific forecasts. Percentage changes can be amplified by "
            "a small prior-year base, and two annual observations do not prove "
            "a persistent trend. Validate national signals against state-level "
            "employer and workforce evidence before drawing local conclusions.",
        ]
    )
    return "\n".join(answer)


def generate_answer(
    question: str,
    context: str
) -> str:

    question = question.strip()

    if not question:
        return "Please enter a question."

    blocks = extract_data(context)

    if not blocks:
        return (
            "I couldn't retrieve the required SkillPulse datasets. "
            "Please check whether the backend data services are working."
        )

    intent = detect_intent(question)

    q = question.lower()

    if intent == "state_analysis":
        return generate_state_analysis(blocks)

    # Select relevant datasets.

    if intent == "forecast":
        keywords = ["forecast", "prediction", "trend"]

    elif intent == "demand":
        keywords = ["vacancy", "sector", "demand", "ncs"]

    elif intent == "employment":
        keywords = ["employment", "wpr", "plfs", "industry"]

    elif intent == "skills":
        keywords = ["skill", "qualification", "vacancy"]

    else:
        keywords = [
            "overview", "employment",
            "vacancy", "industry"
        ]

    selected = []

    for block in blocks:

        title = block["title"].lower()

        if any(keyword in title for keyword in keywords):
            selected.append(block)

    # Forecast-specific response.

    if intent == "forecast":
        forecast_blocks = [
            b for b in blocks
            if "forecast" in b["title"].lower()
        ]

        if not forecast_blocks:
            return (
                "SkillPulse currently has no available forecasting "
                "result for this question. Historical observations "
                "are available, but I won't present them as future predictions."
            )
        return generate_forecast_interpretation(forecast_blocks[0]["data"])

    if not selected:
        selected = blocks[:3]

    response = [
        "SKILLPULSE INTELLIGENCE ANALYSIS",
        ""
    ]

    if intent == "skills":

        response.append(
            "SKILL DEVELOPMENT ANALYSIS\n"
            "Recommendations should be aligned with the available "
            "sector vacancy and qualification data."
        )

    elif intent == "demand":

        response.append("SECTOR AND VACANCY ANALYSIS")

    elif intent == "employment":

        response.append("EMPLOYMENT ANALYSIS")

    else:

        response.append(
            "Here is the available labour-market information."
        )

    response.append("")

    for block in selected[:5]:

        response.append(f"--- {block['title']} ---")

        records = flatten_data(block["data"])

        if not records:

            response.append("No records available.")
            continue

        # Find rows relevant to the user's question.

        matching = []

        for record in records:

            text = json.dumps(
                record,
                default=str
            ).lower()

            if any(
                word in text
                for word in q.split()
                if len(word) > 3
            ):
                matching.append(record)

        rows = matching if matching else records

        for record in rows[:4]:

            response.append(format_record(record))
            response.append("")

    response.append(
        "DATA LIMITATION: PLFS employment indicators and NCS "
        "platform vacancies measure different things. They should "
        "not automatically be treated as direct skill-gap measurements."
    )

    return "\n".join(response)


async def ask_ai(question: str, context: str = "") -> str:

    return generate_answer(question, context)