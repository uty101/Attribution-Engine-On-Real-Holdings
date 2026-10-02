# Dependencies
Project 3 is a git dependency pinned to commit 88e865d8202023cd495dd9866c49e6adbc9f4654 for pc.cov.cov_lw_cc, pc.cov.condition_cov, pc.cov.window_daily and pc.stats.stationary_bootstrap_indices.
pc.cov.estimate_cov is not used because it needs project 3's config.
Project 1 is dropped: holdings-based exposures come from each stock's own 36-month factor betas, not characteristic z-scores.
Reports use reportlab with invariant=1 instead of weasyprint, which needs GTK and Pango on Windows.
