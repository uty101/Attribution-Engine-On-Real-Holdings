import tomllib
from datetime import date, timedelta
from pathlib import Path

from attrib.config import load_config

CONFIG = Path(__file__).resolve().parents[1] / "config.toml"

# Every key written in kickoff Section 7, as dotted paths.
SPEC_KEYS = {
    "run.bootstrap_seed",
    "sample.first_holdings_date",
    "sample.last_holdings_date",
    "sample.last_return_date",
    "sample.price_start",
    "sample.price_end_exclusive",
    "entities.akre.type",
    "entities.akre.cik",
    "entities.akre.nav_ticker",
    "entities.akre.benchmark",
    "entities.jensen.type",
    "entities.jensen.cik",
    "entities.jensen.nav_ticker",
    "entities.jensen.benchmark",
    "entities.polen.type",
    "entities.polen.cik",
    "entities.polen.nav_ticker",
    "entities.polen.benchmark",
    "entities.ivv.type",
    "entities.ivv.etf_ticker",
    "entities.iwf.type",
    "entities.iwf.etf_ticker",
    "edgar.min_interval_s",
    "edgar.retries",
    "edgar.backoff_s",
    "edgar.units_switch_date",
    "edgar.implied_price_lo",
    "edgar.implied_price_hi",
    "openfigi.batch_no_key",
    "openfigi.batch_with_key",
    "openfigi.min_interval_no_key_s",
    "openfigi.min_interval_with_key_s",
    "gates.fund_nav_corr_min",
    "gates.benchmark_gap_max",
    "linking.zero_tol",
    "factors.names",
    "factors.hac_maxlags",
    "factors.rolling_window",
    "factors.stock_beta_window",
    "factors.stock_beta_min_obs",
    "risk.cov_months",
    "risk.daily_to_monthly",
    "risk.months_per_year",
    "risk.max_cond",
    "risk.top_n_positions",
    "bootstrap.mean_block",
    "bootstrap.reps",
    "bootstrap.lo",
    "bootstrap.hi",
    "report.dpi",
    "report.max_pages",
}


def _dotted(d: dict, prefix: str = "") -> set[str]:
    out = set()
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out |= _dotted(v, key + ".")
        else:
            out.add(key)
    return out


def _is_quarter_end(d: date) -> bool:
    return d.month in (3, 6, 9, 12) and (d + timedelta(days=1)).day == 1


def test_keys_match_spec_both_ways():
    with open(CONFIG, "rb") as f:
        keys = _dotted(tomllib.load(f))
    assert keys - SPEC_KEYS == set()
    assert SPEC_KEYS - keys == set()
    cfg = load_config(CONFIG)
    assert list(cfg.entities) == ["akre", "jensen", "polen", "ivv", "iwf"]


def test_fund_benchmarks_exist():
    cfg = load_config(CONFIG)
    funds = [e for e in cfg.entities.values() if e.type == "fund"]
    assert funds
    for e in funds:
        assert e.benchmark in cfg.entities
        assert cfg.entities[e.benchmark].type == "benchmark"


def test_dates_parse_and_are_quarter_ends():
    with open(CONFIG, "rb") as f:
        raw = tomllib.load(f)["sample"]
    parsed = {k: date.fromisoformat(v) for k, v in raw.items()}
    s = load_config(CONFIG).sample
    for k, d in parsed.items():
        assert getattr(s, k) == d
    for k in ("first_holdings_date", "last_holdings_date", "last_return_date"):
        assert _is_quarter_end(parsed[k]), k
    assert parsed["price_end_exclusive"] - timedelta(days=1) == parsed["last_return_date"]
