from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from questions.provider_catalog import resolve_model

MIN_GROSS_MARGIN = 0.25
UPSTREAM_MARKUP = 1.55
OPENROUTER_FEE = 1.055
MICRO = 1_000_000

LANE_LOCAL = "local"
LANE_RUNPOD = "runpod"
LANE_UPSTREAM = "upstream"
LANE_OPENROUTER = "openrouter"

OVERFLOW_TIERS = frozenset({"paid", "sub"})

PLAN_PRICE_CENTS = 1900
LITE_PLAN_PRICE_CENTS = 900
STRIPE_FEE_PCT = 0.029
STRIPE_FEE_FIXED_CENTS = 30
SUB_INCLUDED_COST_CENTS = 1000
LITE_INCLUDED_COST_CENTS = 400


@dataclass(frozen=True)
class GpuLaneCost:
    gpu_hour_usd: float
    decode_tok_s: float
    prefill_tok_s: float
    utilization: float

    def per_mtok(self) -> tuple[float, float]:
        busy_hours = self.utilization * 3600 / 1e6
        return (
            self.gpu_hour_usd / (self.prefill_tok_s * busy_hours),
            self.gpu_hour_usd / (self.decode_tok_s * busy_hours),
        )


LOCAL_5090 = GpuLaneCost(gpu_hour_usd=0.40, decode_tok_s=160.0, prefill_tok_s=2000.0, utilization=0.50)
RUNPOD_4090 = GpuLaneCost(gpu_hour_usd=1.10, decode_tok_s=1200.0, prefill_tok_s=8000.0, utilization=0.15)

VOLUME_TIERS: tuple[tuple[str, int, float], ...] = (
    ("payg", 0, 0.00),
    ("builder", 5_000, 0.03),
    ("scale", 25_000, 0.05),
    ("volume", 100_000, 0.08),
)
MAX_DISCOUNT = max(t[2] for t in VOLUME_TIERS)


def _ceil_cent(x: float) -> float:
    return math.ceil(x * 100 - 1e-9) / 100


def _floor_list(cost: float) -> float:
    return _ceil_cent(cost / ((1 - MIN_GROSS_MARGIN) * (1 - MAX_DISCOUNT)))


def _lane_costs() -> dict[str, tuple[float, float]]:
    return {LANE_LOCAL: LOCAL_5090.per_mtok(), LANE_RUNPOD: RUNPOD_4090.per_mtok()}


GPU_LANE_COST: dict[str, tuple[float, float]] = _lane_costs()
GPU_LANE_LIST: dict[str, tuple[float, float]] = {
    lane: (_floor_list(c[0]), _floor_list(c[1])) for lane, c in GPU_LANE_COST.items()
}


def tier_for_prepaid(prepaid_cents_90d: int) -> tuple[str, float]:
    name, disc = VOLUME_TIERS[0][0], VOLUME_TIERS[0][2]
    for tname, minimum, d in VOLUME_TIERS:
        if prepaid_cents_90d >= minimum:
            name, disc = tname, d
    return name, disc


def tier_discount(tier_name: str) -> float:
    for tname, _, d in VOLUME_TIERS:
        if tname == tier_name:
            return d
    return 0.0


def overflow_allowed(request_tier: Optional[str]) -> bool:
    return request_tier in OVERFLOW_TIERS


def lane_for(model_id: str, overflowed: bool = False) -> str:
    model = resolve_model(model_id)
    if model is None:
        return LANE_RUNPOD if overflowed else LANE_LOCAL
    if model.provider == "openrouter" or model.id.startswith("or/") or model.provider_model_id.startswith("or/"):
        return LANE_OPENROUTER
    return LANE_UPSTREAM


def cost_per_mtok(model_id: str, lane: str) -> tuple[float, float]:
    if lane in GPU_LANE_COST:
        return GPU_LANE_COST[lane]
    model = resolve_model(model_id)
    if model is None:
        return GPU_LANE_COST[LANE_LOCAL]
    factor = OPENROUTER_FEE if lane == LANE_OPENROUTER else 1.0
    return model.input_price * factor, model.output_price * factor


def list_price_per_mtok(model_id: str, lane: str) -> tuple[float, float]:
    if lane in GPU_LANE_LIST:
        return GPU_LANE_LIST[lane]
    model = resolve_model(model_id)
    if model is None:
        return GPU_LANE_LIST[LANE_LOCAL]
    return round(model.input_price * UPSTREAM_MARKUP, 4), round(model.output_price * UPSTREAM_MARKUP, 4)


def price_per_mtok(model_id: str, lane: str, tier_name: str = "payg") -> tuple[float, float]:
    i, o = list_price_per_mtok(model_id, lane)
    d = tier_discount(tier_name)
    return i * (1 - d), o * (1 - d)


def usage_tokens(usage: Optional[Mapping[str, Any]]) -> tuple[int, int]:
    usage = usage or {}
    p = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
    c = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
    if not p and not c:
        c = int(usage.get("total_tokens") or 0)
    return p, c


def estimate_tokens(text: str) -> int:
    return max(0, math.ceil(len(text or "") / 4))


def cost_micro(model_id: str, lane: str, prompt_tokens: int, completion_tokens: int) -> int:
    ci, co = cost_per_mtok(model_id, lane)
    return int(round((prompt_tokens * ci + completion_tokens * co) * 100))


def charge_micro(model_id: str, lane: str, tier_name: str, prompt_tokens: int, completion_tokens: int) -> int:
    pi, po = price_per_mtok(model_id, lane, tier_name)
    return int(math.ceil((prompt_tokens * pi + completion_tokens * po) * 100 - 1e-9))


def gross_margin(model_id: str, lane: str, tier_name: str) -> float:
    ci, co = cost_per_mtok(model_id, lane)
    pi, po = price_per_mtok(model_id, lane, tier_name)
    ratios = [1 - c / p for c, p in ((ci, pi), (co, po)) if p > 0]
    return min(ratios) if ratios else 1.0


def net_plan_revenue_cents(plan_cents: int, percent_off: float = 0.0) -> float:
    gross = plan_cents * (1 - percent_off)
    return gross - (gross * STRIPE_FEE_PCT + STRIPE_FEE_FIXED_CENTS)


def coupon_margin_negative(cost_30d_cents: float, plan_cents: int = PLAN_PRICE_CENTS, percent_off: float = 0.5) -> bool:
    return cost_30d_cents > net_plan_revenue_cents(plan_cents, percent_off)


def included_cost_cents(plan_cents: int) -> int:
    return LITE_INCLUDED_COST_CENTS if plan_cents <= LITE_PLAN_PRICE_CENTS else SUB_INCLUDED_COST_CENTS


def catalog_table() -> list[dict[str, Any]]:
    rows = []
    for lane, (i, o) in GPU_LANE_LIST.items():
        ci, co = GPU_LANE_COST[lane]
        rows.append({"lane": lane, "cost_in": ci, "cost_out": co, "list_in": i, "list_out": o})
    return rows
