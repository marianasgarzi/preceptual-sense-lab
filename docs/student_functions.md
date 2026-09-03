# Implemented Function Reference

This document summarizes the completed experiment helpers retained by the page scaffolds.
The function names remain stable because the experiment pages and existing checks use them.

## Vision: Contrast Sensitivity

- `student_build_preview_triplets(...)` creates deterministic letter sequences.
- `student_compute_contrast_levels(...)` creates the decreasing log-spaced schedule.
- `student_advance_contrast_state(...)` advances a completed contrast level.
- `student_compute_log_contrast_sensitivity(...)` converts the final percentage threshold.

Each level is passed after two correct identifications and failed after two incorrect
identifications, requiring no more than three attempts. The threshold is the lowest level
passed reliably.

## Vision: Tumbling E

- Geometry validation protects the pixel-pitch and visual-angle calculations.
- Trial formatting records full optotype size, one-fifth critical-feature width, response,
  correctness, and angular resolution.
- The exact visual-angle calculation reports resolution in arcminutes.

The configured schedule stops at a 5 px full E, where each unit of its 5×5 grid occupies
one physical display pixel.

## Hearing: Pitch Frequency Range

- Audio validation enforces configured frequency and amplitude limits.
- Audible-bound estimation returns the minimum and maximum probes marked heard, or no bound
  when none was heard.

## Shared Adaptive 3AFC Helpers

The shared helpers validate stimuli, build a three-item mask containing one target, summarize
accuracy, and plot distinct correct and incorrect responses with a threshold line. Runtime
reversal detection and final threshold calculation remain authoritative in
`utils/adaptive_3afc.py`.
