"""Load `config.toml` into frozen dataclasses, one per config table (kickoff Section 7)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Run:
    bootstrap_seed: int


@dataclass(frozen=True)
class Sample:
    first_holdings_date: date
    last_holdings_date: date
    last_return_date: date
    price_start: date
    price_end_exclusive: date


@dataclass(frozen=True)
class Entity:
    id: str
    type: str
    cik: int | None = None
    nav_ticker: str | None = None
    benchmark: str | None = None
    etf_ticker: str | None = None


@dataclass(frozen=True)
class Edgar:
    min_interval_s: float
    retries: int
    backoff_s: tuple[float, ...]
    units_switch_date: date
    implied_price_lo: float
    implied_price_hi: float
    timeout_s: float


@dataclass(frozen=True)
class OpenFigi:
    batch_no_key: int
    batch_with_key: int
    min_interval_no_key_s: float
    min_interval_with_key_s: float


@dataclass(frozen=True)
class Gates:
    fund_nav_corr_min: float
    benchmark_gap_max: float


@dataclass(frozen=True)
class Linking:
    zero_tol: float


@dataclass(frozen=True)
class Factors:
    names: tuple[str, ...]
    hac_maxlags: int
    rolling_window: int
    stock_beta_window: int
    stock_beta_min_obs: int


@dataclass(frozen=True)
class Risk:
    cov_months: int
    daily_to_monthly: int
    months_per_year: int
    max_cond: float
    top_n_positions: int


@dataclass(frozen=True)
class Bootstrap:
    mean_block: int
    reps: int
    lo: float
    hi: float


@dataclass(frozen=True)
class Report:
    dpi: int
    max_pages: int


@dataclass(frozen=True)
class Config:
    run: Run
    sample: Sample
    entities: dict[str, Entity]
    edgar: Edgar
    openfigi: OpenFigi
    gates: Gates
    linking: Linking
    factors: Factors
    risk: Risk
    bootstrap: Bootstrap
    report: Report


def _dates(table: dict) -> dict:
    return {k: date.fromisoformat(v) for k, v in table.items()}


def load_config(path: str | Path = "config.toml") -> Config:
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    edgar = dict(raw["edgar"])
    edgar["backoff_s"] = tuple(float(x) for x in edgar["backoff_s"])
    edgar["units_switch_date"] = date.fromisoformat(edgar["units_switch_date"])
    factors = dict(raw["factors"])
    factors["names"] = tuple(factors["names"])
    return Config(
        run=Run(**raw["run"]),
        sample=Sample(**_dates(raw["sample"])),
        # dict preserves file order: akre, jensen, polen, ivv, iwf
        entities={k: Entity(id=k, **v) for k, v in raw["entities"].items()},
        edgar=Edgar(**edgar),
        openfigi=OpenFigi(**raw["openfigi"]),
        gates=Gates(**raw["gates"]),
        linking=Linking(**raw["linking"]),
        factors=Factors(**factors),
        risk=Risk(**raw["risk"]),
        bootstrap=Bootstrap(**raw["bootstrap"]),
        report=Report(**raw["report"]),
    )
