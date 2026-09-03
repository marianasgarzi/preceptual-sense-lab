"""Validated helpers shared by the three adaptive 3AFC experiment pages."""

import math
import statistics

import streamlit as st


def _history_level(item: dict) -> float | None:
    """Return a finite level from either supported history schema."""
    value = item.get("level", item.get("Level"))
    try:
        level = float(value)
    except (TypeError, ValueError):
        return None
    return level if math.isfinite(level) else None


def _history_correct(item: dict) -> bool:
    """Normalize correctness values used by runtime and preview histories."""
    value = item.get("correct", item.get("Correct", False))
    if isinstance(value, str):
        return value.strip().lower() in {"yes", "true", "correct", "1"}
    return bool(value)


def shared_student_apply_reversal_update(
    *,
    current_level: float,
    step: float,
    is_correct: bool,
    correct_streak: int,
    down_n: int,
    min_level: float,
    max_level: float,
) -> tuple[float, int]:
    """Apply one 2-down/1-up staircase update.

    Inputs:
        current_level: current adaptive stimulus level.
        step: step size for level change.
        is_correct: whether the response is correct.
        correct_streak: consecutive correct count before this trial.
        down_n: number of correct responses needed to step down.
        min_level: minimum allowed level.
        max_level: maximum allowed level.

    Returns:
        Tuple `(next_level, next_correct_streak)` after one update.

    Safety requirements:
        - Clamp level to `[min_level, max_level]`.
        - Treat `down_n < 1` as 1 to avoid zero-step loops.
    """
    lower = float(min_level)
    upper = float(max_level)
    if not all(math.isfinite(value) for value in (lower, upper)):
        return float(current_level), max(0, int(correct_streak))
    if lower > upper:
        lower, upper = upper, lower

    level = float(current_level)
    if not math.isfinite(level):
        level = lower
    level = max(lower, min(upper, level))

    safe_step = abs(float(step))
    if not math.isfinite(safe_step):
        safe_step = 0.0
    safe_down_n = max(1, int(down_n))
    streak = max(0, int(correct_streak))

    if is_correct:
        streak += 1
        if streak >= safe_down_n:
            level -= safe_step
            streak = 0
    else:
        level += safe_step
        streak = 0

    return max(lower, min(upper, level)), streak


def shared_student_plot_staircase(
    history: list[dict], threshold: float, y_label: str, title: str
) -> None:
    """Plot the staircase trace for the given history.

    Expected plot content:
        - X-axis: trial number.
        - Y-axis: level value per trial.
        - Visual distinction for correct vs incorrect trials.
        - Threshold drawn as a horizontal dashed line.

    Safety requirements:
        - Do not crash for empty or very short history lists.
    """
    valid_trials: list[int] = []
    valid_levels: list[float] = []
    valid_correct: list[bool] = []
    for fallback_trial, item in enumerate(history, start=1):
        level = _history_level(item)
        if level is None:
            continue
        trial_value = item.get("trial", item.get("Trial", fallback_trial))
        try:
            trial = int(trial_value)
        except (TypeError, ValueError):
            trial = fallback_trial
        valid_trials.append(trial)
        valid_levels.append(level)
        valid_correct.append(_history_correct(item))

    if not valid_levels:
        st.info("No staircase trials are available to plot yet.")
        return

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        st.info("Matplotlib plot unavailable in this environment.")
        return

    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.plot(valid_trials, valid_levels, color="#1565C0", linewidth=1.6, label="Level")

    correct_trials = [
        trial for trial, correct in zip(valid_trials, valid_correct, strict=True) if correct
    ]
    correct_levels = [
        level for level, correct in zip(valid_levels, valid_correct, strict=True) if correct
    ]
    incorrect_trials = [
        trial for trial, correct in zip(valid_trials, valid_correct, strict=True) if not correct
    ]
    incorrect_levels = [
        level for level, correct in zip(valid_levels, valid_correct, strict=True) if not correct
    ]
    if correct_trials:
        ax.scatter(correct_trials, correct_levels, color="#2E7D32", s=28, label="Correct")
    if incorrect_trials:
        ax.scatter(
            incorrect_trials,
            incorrect_levels,
            color="#C62828",
            marker="x",
            s=36,
            label="Incorrect",
        )

    try:
        safe_threshold = float(threshold)
    except (TypeError, ValueError):
        safe_threshold = math.nan
    if math.isfinite(safe_threshold):
        ax.axhline(
            safe_threshold,
            color="#6A1B9A",
            linestyle="--",
            linewidth=1.3,
            label=f"Estimated threshold: {safe_threshold:.2f}",
        )
    ax.set_xlabel("Trial Number")
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.grid(alpha=0.25)
    ax.legend(loc="best")
    st.pyplot(fig)
    plt.close(fig)


def shared_student_build_three_interval_targets(*, target_index: int) -> list[bool]:
    """Build a length-3 target mask with exactly one `True` entry.

    Example:
        target_index=1 -> [False, True, False]
    """
    try:
        index = int(target_index)
    except (TypeError, ValueError):
        index = 0
    index = max(0, min(2, index))
    return [position == index for position in range(3)]


def shared_student_update_staircase_state(
    *,
    current_level: float,
    step: float,
    is_correct: bool,
    correct_streak: int,
    down_n: int,
    min_level: float,
    max_level: float,
) -> tuple[float, int]:
    """Reusable helper that keeps staircase behavior consistent.

    This can wrap or share logic with `shared_student_apply_reversal_update`.
    """
    return shared_student_apply_reversal_update(
        current_level=current_level,
        step=step,
        is_correct=is_correct,
        correct_streak=correct_streak,
        down_n=down_n,
        min_level=min_level,
        max_level=max_level,
    )


def shared_student_estimate_threshold_from_reversals(
    *, reversals: list[float], fallback_level: float, tail_count: int = 4
) -> float:
    """Estimate threshold using the trailing reversal points.

    Recommended behavior:
        - When there are enough reversals, average the last `tail_count` values.
        - Otherwise return `fallback_level`.
    """
    safe_tail_count = max(1, int(tail_count))
    finite_reversals = []
    for value in reversals:
        try:
            reversal = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(reversal):
            finite_reversals.append(reversal)
    if len(finite_reversals) >= safe_tail_count:
        return float(statistics.mean(finite_reversals[-safe_tail_count:]))
    return float(fallback_level)


def shared_student_compute_recent_accuracy(history: list[dict], window: int = 12) -> float:
    """Compute a trailing percent-correct accuracy metric.

    Output should be a percentage in the `[0, 100]` range.
    """
    if not history:
        return 0.0
    safe_window = max(1, int(window))
    recent = history[-safe_window:]
    accuracy = 100.0 * statistics.mean(
        1.0 if _history_correct(item) else 0.0 for item in recent
    )
    return max(0.0, min(100.0, float(accuracy)))


def shared_student_validate_audio_params(*, amplitude: float, stimulus_value: float) -> bool:
    """Validate amplitude and stimulus-specific numeric values.

    Returns:
        `True` when inputs are in safe ranges, otherwise `False`.
    """
    try:
        safe_amplitude = float(amplitude)
        safe_stimulus = float(stimulus_value)
    except (TypeError, ValueError):
        return False
    return (
        math.isfinite(safe_amplitude)
        and math.isfinite(safe_stimulus)
        and 0.0 < safe_amplitude <= 1.0
        and safe_stimulus >= 0.0
    )


def shared_student_plot_staircase_with_threshold(
    *, history: list[dict], threshold: float, y_label: str, title: str
) -> None:
    """Wrapper that draws the staircase and highlights the threshold.

    Implementation:
        Call `shared_student_plot_staircase(...)` internally to avoid duplicate code.
    """
    shared_student_plot_staircase(
        history=history,
        threshold=threshold,
        y_label=y_label,
        title=title,
    )
