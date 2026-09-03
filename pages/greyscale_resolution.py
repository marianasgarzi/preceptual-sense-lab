import math
import random

import streamlit as st

from utils.test_config import load_test_config
from utils.ui import (
    render_instructions,
    render_page_header,
)

st.set_page_config(
    page_title="Contrast Sensitivity Test",
    layout="wide",
)

render_page_header(
    "Contrast Sensitivity Test (Pelli-Style)",
    "Single-letter Pelli-style progression with fixed log contrast steps.",
    "greyscale",
)

render_instructions(
    "How To Run This Test",
    (
        "This version follows a strict Pelli-style progression (no 3AFC). "
        "One letter is shown at a time while contrast decreases by a fixed log step."
    ),
    [
        "This educational activity is not a medical diagnostic test.",
        "Keep your normal or corrected-vision condition consistent throughout the test.",
        "Keep viewing distance and screen brightness reasonably constant.",
        (
            "Type the letter you see. Each contrast level uses up to three letters and "
            "requires two correct identifications to pass."
        ),
        "You may stop at any time by returning Home; responses stay in this local session.",
    ],
)

config = load_test_config()
cfg = config["greyscale"]
letters = cfg["letters"]
row_count = int(cfg["preview"]["rows"])
log_step = float(cfg["preview"]["log_contrast_step"])


def student_build_preview_triplets(
    *,
    letters_pool: str,
    rows: int,
    seed: int,
) -> list[str]:
    """generate a deterministic preview chart.

    Return exactly `rows` strings, each three letters long, sampled from
    `letters_pool` using a RNG initialized with `seed`. This helper keeps the
    view consistent across reruns.

    If `rows <= 0` or `letters_pool` is empty, return an empty list.
    """
    if rows <= 0 or not letters_pool:
        return []
    rng = random.Random(seed)
    return ["".join(rng.choice(letters_pool) for _ in range(3)) for _ in range(rows)]


def student_compute_contrast_levels(*, rows: int, step_log10: float) -> list[float]:
    """return a log-spaced contrast schedule in percent.

    Use `contrast_percent = 100 * 10 ** (-(row_index * step_log10))` for
    row_index 0..rows‑1. If `rows <= 0`, return an empty list.
    """
    if rows <= 0:
        return []
    if not math.isfinite(step_log10) or step_log10 <= 0.0:
        raise ValueError("The log contrast step must be a positive finite number.")
    return [100.0 * 10 ** (-(row_index * step_log10)) for row_index in range(rows)]


def student_advance_contrast_state(
    *,
    trial_index: int,
    response_yes: bool,
    total_levels: int,
) -> tuple[int, bool]:
    """advance the trial index or finish the run.

    Return `(next_index, finished)`. Finish if `response_yes` is False or when
    advancing goes beyond `total_levels - 1`. Clamp `next_index` to valid range.
    """
    if total_levels <= 0:
        return 0, True
    safe_index = max(0, min(int(trial_index), total_levels - 1))
    if not response_yes or safe_index >= total_levels - 1:
        return safe_index, True
    return safe_index + 1, False


def student_compute_log_contrast_sensitivity(threshold_percent: float) -> float:
    """convert percent threshold to log contrast sensitivity.

    Use `log10(1 / (threshold_percent / 100))` and guard against zero or
    negative thresholds to avoid math errors.
    """
    if not math.isfinite(threshold_percent) or threshold_percent <= 0.0:
        return 0.0
    return math.log10(1.0 / (threshold_percent / 100.0))



contrast_levels_pct = student_compute_contrast_levels(rows=row_count, step_log10=log_step)
preview_triplets = student_build_preview_triplets(
    letters_pool=letters,
    rows=row_count,
    seed=int(cfg["preview"]["seed"]),
)

if len(contrast_levels_pct) != row_count or len(preview_triplets) != row_count:
    st.error("Student function outputs are invalid. Check list lengths and return values.")
    st.stop()


def draw_letter_card(letter: str, contrast_pct: float) -> str:
    bg = int(cfg["background_rgb"])
    contrast = max(0.0, min(1.0, contrast_pct / 100.0))
    fg = int(max(0, min(255, bg * (1.0 - contrast))))
    return (
        "<div style='background:rgb(255,255,255); border:1px solid #d3d3d3; border-radius:10px; "
        "padding:1rem 0.5rem; text-align:center;'>"
        f"<div style='font-size:3rem; font-weight:700; color:rgb({fg},{fg},{fg}); "
        "font-family:serif;'>"
        f"{letter}</div></div>"
    )


if "greyscale_pelli_index" not in st.session_state:
    st.session_state["greyscale_pelli_index"] = 0
if "greyscale_pelli_trial_letters" not in st.session_state:
    trial_rng = random.Random(int(cfg["preview"]["seed"]) + 1)
    st.session_state["greyscale_pelli_trial_letters"] = [
        trial_rng.choice(letters) for _ in range(len(contrast_levels_pct) * 3)
    ]
if "greyscale_pelli_history" not in st.session_state:
    st.session_state["greyscale_pelli_history"] = []
if "greyscale_pelli_finished" not in st.session_state:
    st.session_state["greyscale_pelli_finished"] = False
if "greyscale_pelli_threshold_pct" not in st.session_state:
    st.session_state["greyscale_pelli_threshold_pct"] = None
if "greyscale_pelli_completion_reason" not in st.session_state:
    st.session_state["greyscale_pelli_completion_reason"] = None
if "greyscale_pelli_level_attempts" not in st.session_state:
    st.session_state["greyscale_pelli_level_attempts"] = 0
if "greyscale_pelli_level_correct" not in st.session_state:
    st.session_state["greyscale_pelli_level_correct"] = 0

with st.container(border=True):
    st.subheader("Contrast Schedule")
    st.caption(
        f"{len(contrast_levels_pct)} levels decrease by {log_step:.2f} log10 units per trial, "
        f"from {contrast_levels_pct[0]:.2f}% to {contrast_levels_pct[-1]:.2f}% contrast."
    )

trial_index = int(st.session_state["greyscale_pelli_index"])
finished = bool(st.session_state["greyscale_pelli_finished"])
current_contrast_pct = contrast_levels_pct[min(trial_index, len(contrast_levels_pct) - 1)]
trial_number = len(st.session_state["greyscale_pelli_history"]) + 1
letter_index = min(
    trial_number - 1,
    len(st.session_state["greyscale_pelli_trial_letters"]) - 1,
)
current_letter = st.session_state["greyscale_pelli_trial_letters"][letter_index]
level_attempts = int(st.session_state["greyscale_pelli_level_attempts"])
level_correct = int(st.session_state["greyscale_pelli_level_correct"])

with st.container(border=True):
    st.subheader("Single-Letter Trial")
    st.caption(f"Current level: {trial_index + 1}/{len(contrast_levels_pct)}")
    st.caption(
        f"Reliability check at this level: {level_correct} correct in "
        f"{level_attempts} attempt(s); two correct responses pass the level."
    )
    st.caption(f"Current contrast: {current_contrast_pct:.2f}%")
    st.markdown(draw_letter_card(current_letter, current_contrast_pct), unsafe_allow_html=True)

with st.container(border=True):
    st.subheader("Respond")
    response = st.text_input(
        "Type the letter shown",
        max_chars=1,
        key=f"greyscale_pelli_response_{trial_number}",
        disabled=finished,
    )
    submitted = st.button(
        "Submit Response",
        type="primary",
        width="stretch",
        disabled=finished,
    )
    if submitted and not finished:
        normalized_response = response.strip().upper()
        is_correct = normalized_response == current_letter.upper()
        st.session_state["greyscale_pelli_history"].append(
            {
                "Trial": trial_number,
                "Contrast Level": trial_index + 1,
                "Attempt at Level": level_attempts + 1,
                "Presented Stimulus": current_letter,
                "Contrast (%)": round(current_contrast_pct, 2),
                "Participant Response": normalized_response or "(blank)",
                "Correct": "Yes" if is_correct else "No",
            }
        )

        updated_attempts = level_attempts + 1
        updated_correct = level_correct + int(is_correct)
        updated_incorrect = updated_attempts - updated_correct
        level_passed = updated_correct >= 2
        level_failed = updated_incorrect >= 2

        if level_passed:
            st.session_state["greyscale_pelli_threshold_pct"] = current_contrast_pct
            next_index, next_finished = student_advance_contrast_state(
                trial_index=trial_index,
                response_yes=True,
                total_levels=len(contrast_levels_pct),
            )
            st.session_state["greyscale_pelli_index"] = next_index
            st.session_state["greyscale_pelli_finished"] = next_finished
            st.session_state["greyscale_pelli_level_attempts"] = 0
            st.session_state["greyscale_pelli_level_correct"] = 0
            if next_finished:
                st.session_state["greyscale_pelli_completion_reason"] = "schedule_complete"
        elif level_failed:
            st.session_state["greyscale_pelli_finished"] = True
            st.session_state["greyscale_pelli_completion_reason"] = (
                "reliability_failure"
            )
            st.session_state["greyscale_pelli_level_attempts"] = updated_attempts
            st.session_state["greyscale_pelli_level_correct"] = updated_correct
        else:
            st.session_state["greyscale_pelli_level_attempts"] = updated_attempts
            st.session_state["greyscale_pelli_level_correct"] = updated_correct
        st.rerun()

threshold_value = st.session_state["greyscale_pelli_threshold_pct"]

with st.container(border=True):
    st.subheader("Results")
    if not finished:
        if threshold_value is None:
            st.caption("Test in progress. No provisional threshold is available yet.")
        else:
            st.metric(
                "Provisional Lowest Correct Contrast (%)",
                f"{float(threshold_value):.2f}",
            )
            st.caption("This is an in-progress value, not a final result.")
    elif threshold_value is None:
        st.subheader("Test Complete")
        st.warning(
            "The first contrast level was not identified reliably (two errors before "
            "two correct responses), so a threshold could not be established within "
            "this schedule."
        )
        st.caption(
            "For the assignment report, document the session's visual condition "
            "(unaided, glasses, contacts, or other) without recording a diagnosis."
        )
    else:
        st.subheader("Test Complete")
        threshold_pct = float(threshold_value)
        contrast_sensitivity = 100.0 / threshold_pct
        log_cs = student_compute_log_contrast_sensitivity(threshold_pct)
        distinguishable_steps = max(1, round(100.0 / threshold_pct))
        perceptual_information_bits = math.log2(distinguishable_steps)

        st.success("Pelli-style run complete.")
        col_1, col_2, col_3 = st.columns(3)
        col_1.metric("Final Contrast Threshold", f"{threshold_pct:.2f}%")
        col_2.metric("Contrast Sensitivity (1/threshold)", f"{contrast_sensitivity:.1f}")
        col_3.metric("Log Contrast Sensitivity", f"{log_cs:.2f}")

        st.subheader("Approximate Display-Resolution Interpretation")
        st.write(
            f"A {threshold_pct:.2f}% threshold corresponds to roughly "
            f"{distinguishable_steps} threshold-sized intensity differences across a "
            "0–100% range under these viewing conditions. Encoding that many perceptually "
            f"distinguishable steps would require about {perceptual_information_bits:.1f} "
            "bits of information, but this is not a measurement of the display's hardware "
            "bit depth."
        )
        st.write(
            "For comparison, an 8-bit display provides 256 digital code levels per channel "
            "(about 0.39% per code step). The assignment's approximately 4% perceptual "
            "difference example spans about ten 8-bit code steps and implies roughly 25 "
            "perceptually distinguishable intensity differences—not that the display is a "
            "5-bit device. Display calibration, luminance, ambient light, adaptation, and "
            "the eye's nonlinear response all affect this relationship."
        )

        st.subheader("Human-Factors Interpretation")
        st.write(
            "Contrast thresholds affect display legibility and visual ergonomics. Text, "
            "controls, and status indicators near a person's threshold may be tiring or "
            "inaccessible, especially under glare, fatigue, or reduced vision. Accessible "
            "interfaces should therefore avoid relying on subtle low-contrast differences "
            "and should provide generous contrast rather than treating this estimate as a "
            "design minimum."
        )
        st.caption(
            "For the assignment report, document the session's visual condition "
            "(unaided, glasses, contacts, or other) without recording a diagnosis."
        )

with st.container(border=True):
    st.subheader("Trial Log")
    history = st.session_state["greyscale_pelli_history"]
    if history:
        st.dataframe(history, width="stretch", hide_index=True)
    else:
        st.caption("No responses yet.")

with st.container(border=True):
    st.subheader("Test Controls")

    if st.button("Restart Test", width="stretch"):
        for key in [
            "greyscale_pelli_index",
            "greyscale_pelli_trial_letters",
            "greyscale_pelli_history",
            "greyscale_pelli_finished",
            "greyscale_pelli_threshold_pct",
            "greyscale_pelli_completion_reason",
            "greyscale_pelli_level_attempts",
            "greyscale_pelli_level_correct",
        ]:
            st.session_state.pop(key, None)
        for key in list(st.session_state):
            if key.startswith("greyscale_pelli_response_"):
                st.session_state.pop(key, None)
        st.rerun()
