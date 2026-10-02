# Review — Section 1

## Section

Section 1, Foundation and EDGAR holdings. **Stopped at step 1.3 under rule 4 (kickoff rule 15): `SEC_USER_AGENT` is unset, and step 1.3 is the first step that pulls from EDGAR** (the `--stage fixtures` download). Steps 1.0 to 1.2 are complete. Steps 1.3 to 1.6 are not started.

## Steps completed

- 1.0 apply session 0 decisions (pyproject D-03 and `pymupdf`, lock rebuilt with the D-04 command, `decisions/OPEN.md` emptied, `decisions/section_0_review.md`, `CLAUDE.md` amendments 1 to 4, `PLAN.md` OPEN-NN → D-NN) — `50a2892`
- 1.1 `attrib/config.py` and `tests/test_config.py` — `bf10c0e`
- 1.2 `EdgarClient` in `attrib/edgar.py` and `tests/test_edgar_client.py` — `4b1e319`
- 1.3 not started: stop (see Open questions)
- 1.4 not started
- 1.5 not started
- 1.6 not started

## Evidence

### 1.2 recorded fake-clock sleeps

`pytest -p socket --disable-socket -q -s tests/test_edgar_client.py`:

```
.recorded sleeps: [0.2, 0.2]
.recorded sleeps: [2.0, 4.0]
.recorded sleeps: [2.0, 4.0, 8.0]
.
4 passed in 0.15s
```

In order: `test_min_interval_respected` (3 back-to-back calls, sum 0.4), `test_429_then_200_retries_with_configured_waits` (429, 429, 200), `test_three_failures_raise` (4 × 503). The first line of output is `test_user_agent_header_sent`, which prints nothing.

### Stop evidence: `SEC_USER_AGENT`

Checked in the session process and at Windows user and machine scope before step 1.3; it is set in none of them:

```
SEC_UA set: False                               # $env:SEC_USER_AGENT
[Environment]::GetEnvironmentVariable('SEC_USER_AGENT','User')     -> (empty)
[Environment]::GetEnvironmentVariable('SEC_USER_AGENT','Machine')  -> (empty)
```

No `.env` file exists in the repo or its parent. `OPENFIGI_API_KEY` is also unset (optional, not needed until 2.1).

### Section E items 2 to 8 and 10

Not produced: they all need data from steps 1.3 to 1.6.

## Tests run

`.venv/Scripts/python.exe -m pytest -p socket --disable-socket -q` (CPython 3.12.13, venv from `uv venv --python 3.12`, installed from the new lock):

```
........                                                                 [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:864
  C:\Utkarsh\10. Quant Projects\6) Attribution Engine On Real Holdings\repo-clone\.venv\Lib\site-packages\_pytest\config\__init__.py:864: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
8 passed, 1 warning in 0.12s
```

The warning comes from `-p socket` loading pytest-socket a second time; the plugin is also registered through its entry point. It does not affect the run.

## Fresh-clone check

Clone of the pushed `main` into `C:\t\s1`, `uv venv --python 3.12`, `uv pip install -r requirements-lock.txt`, `uv pip install -e . --no-deps`, `pytest -p socket --disable-socket -q` (install output trimmed to its last line each):

```
4b1e319 step 1.2: EDGAR client with rate limit and retries
Using CPython 3.12.13
Creating virtual environment at: .venv
Activate with: .venv\Scripts\activate
 + yfinance==1.7.0
 + attrib==0.0.0 (from file:///C:/t/s1)
........                                                                 [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:864
  C:\t\s1\.venv\Lib\site-packages\_pytest\config\__init__.py:864: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
8 passed, 1 warning in 0.45s
```

## Runtime per step

- 1.0: lock compile plus venv rebuild, under 1 minute.
- 1.1: suite 0.03 s.
- 1.2: suite 0.80 s.

## Deviations from PLAN.md

- 1.0, item 6: the generic text `**OPEN-NN**` in the `PLAN.md` preamble (line 5) was left as written. It names the marker format rather than marking an item. All 33 numbered markers were replaced with `D-NN`.
- 1.0, item 4: `decisions/section_0_review.md` holds the Section B table only, with no heading, so that it is the table verbatim.

## Not verified

- No EDGAR request was made. The client has run only against the fake session.
- `EdgarClient` passes no `timeout` to `session.get`. No timeout value is set in config or in an instruction file, so none was added (rule 6). A stalled connection would therefore hang. See Open questions.

## Open questions

1. **Stop: `SEC_USER_AGENT` unset.** The owner sets it, in the format `Utkarsh Malhotra <email>`, and the session is rerun from step 1.3. Steps 1.0 to 1.2 do not need to be redone.
2. **HTTP timeout.** Options: (a) add `edgar.timeout_s` to `config.toml` and pass it to `session.get`; (b) keep no timeout, as now.

## Files changed

- `pyproject.toml`, `requirements-lock.txt`, `decisions/OPEN.md`, `decisions/section_0_review.md` (new), `CLAUDE.md`, `PLAN.md` (step 1.0)
- `attrib/config.py` (new), `tests/test_config.py` (new) (step 1.1)
- `attrib/edgar.py` (new), `tests/test_edgar_client.py` (new) (step 1.2)
- `review/section_1.md` (new), `instructions/01_section_1.status.md` (new)

## Reviewer reads

1. `instructions/01_section_1.status.md`
2. `attrib/edgar.py`, then `tests/test_edgar_client.py`
3. `attrib/config.py`, then `tests/test_config.py`
4. `git show 50a2892 -- CLAUDE.md pyproject.toml decisions/OPEN.md`
