import math

import streamlit as st

from pages._shared_3afc_student import (
    shared_student_apply_reversal_update,
    shared_student_build_three_interval_targets,
    shared_student_compute_recent_accuracy,
    shared_student_estimate_threshold_from_reversals,
    shared_student_plot_staircase,
    shared_student_plot_staircase_with_threshold,
    shared_student_update_staircase_state,
    shared_student_validate_audio_params,
)
from utils.adaptive_3afc import (
    estimate_threshold,
    get_or_create_trial,
    init_adaptive_state,
    reset_adaptive_state,
)
from utils.audio_tools import single_tone_wav
from utils.test_config import load_test_config
from utils.three_afc import (
    render_completion_summary,
    render_feedback,
    render_recent_accuracy_metric,
    submit_3afc_response,
)
from utils.ui import (
    render_instructions,
    render_page_header,
)

st.set_page_config(
    page_title="Amplitude Threshold Test",
    layout="wide",
    initial_sidebar_state="collapsed",
)

render_page_header(
    "Amplitude Threshold Test",
    "3AFC adaptive test: identify the interval with higher amplitude.",
    "amplitude",
)

render_instructions(
    "How To Run This Test",
    (
        "You will hear three tones. One tone is slightly louder than the other two. "
        "Select the louder interval in each trial."
    ),
    [
        "This educational activity is not a medical diagnostic test.",
        "Perform the test in a quiet environment.",
        (
            "Begin at a comfortable low volume. Do not increase device or system "
            "volume during the test."
        ),
        "Stop immediately if any sound becomes uncomfortable.",
        "Answer every trial even when unsure (forced choice).",
        "Adaptive step sizes shrink after reversals to stabilize the threshold.",
        "You may stop at any time by returning Home; responses stay in this local session.",
    ],
)

config = load_test_config()
cfg = config["amplitude_discrimination"]
REFERENCE_AMPLITUDE = float(cfg["reference_amplitude"]["min"])
REFERENCE_FREQUENCY_HZ = int(cfg["reference_frequency_hz"]["default"])
TONE_DURATION_S = float(cfg["tone_duration_s"])
MAX_TARGET_AMPLITUDE = 0.8


def student_build_amplitude_intervals_audio(
    *,
    baseline_amplitude: float,
    delta_db: float,
    reference_hz: int,
    target_index: int,
) -> list[bytes]:
    """Build one 3AFC trial audio set for amplitude discrimination.

    Why this function exists:
        Each trial needs exactly three candidate sounds with one target interval.
        This function packages trial generation so the page can remain focused on UI
        and adaptive logic while keeping stimulus creation testable.

    Inputs:
        baseline_amplitude: Reference amplitude for non-target intervals.
        delta_db: Loudness increment in decibels for the target interval.
        reference_hz: Tone frequency used for all intervals.
        target_index: Index (0, 1, or 2) of the louder interval.

    Output:
        A list of exactly 3 WAV byte payloads in interval order.

    Behavior:
        - Convert `delta_db` to an amplitude ratio.
        - Build 3 tones at `reference_hz`.
        - Use baseline amplitude for two intervals.
        - Use louder amplitude for `target_index`.
        - Return WAV bytes compatible with `st.audio`.
    """
    try:
        safe_baseline = float(baseline_amplitude)
        safe_delta_db = float(delta_db)
        safe_reference_hz = float(reference_hz)
    except (TypeError, ValueError) as error:
        raise ValueError("Amplitude stimulus values must be numeric.") from error

    amplitude_limits = cfg["reference_amplitude"]
    frequency_limits = cfg["reference_frequency_hz"]
    delta_limits = cfg["adaptive"]
    ratio = 10 ** (safe_delta_db / 20.0) if math.isfinite(safe_delta_db) else math.inf
    target_amplitude = safe_baseline * ratio
    valid_duration = math.isfinite(TONE_DURATION_S) and 0.0 < TONE_DURATION_S <= 10.0
    if not (
        float(amplitude_limits["min"])
        <= safe_baseline
        <= float(amplitude_limits["max"])
        and float(delta_limits["min_level"])
        <= safe_delta_db
        <= float(delta_limits["max_level"])
        and float(frequency_limits["min"])
        <= safe_reference_hz
        <= float(frequency_limits["max"])
        and valid_duration
        and shared_student_validate_audio_params(
            amplitude=safe_baseline,
            stimulus_value=safe_reference_hz,
        )
        and math.isfinite(target_amplitude)
        and safe_baseline < target_amplitude <= MAX_TARGET_AMPLITUDE
    ):
        raise ValueError("Amplitude, dB difference, frequency, or duration is unsafe.")

    target_mask = shared_student_build_three_interval_targets(target_index=target_index)
    reference_wav = single_tone_wav(
        frequency_hz=safe_reference_hz,
        duration_s=TONE_DURATION_S,
        amplitude=safe_baseline,
    )
    target_wav = single_tone_wav(
        frequency_hz=safe_reference_hz,
        duration_s=TONE_DURATION_S,
        amplitude=target_amplitude,
    )
    return [target_wav if is_target else reference_wav for is_target in target_mask]


def student_apply_reversal_update(
    *,
    current_level: float,
    step: float,
    is_correct: bool,
    correct_streak: int,
    down_n: int,
    min_level: float,
    max_level: float,
) -> tuple[float, int]:
    """Delegate to the shared 3AFC implementation."""
    return shared_student_apply_reversal_update(
        current_level=current_level,
        step=step,
        is_correct=is_correct,
        correct_streak=correct_streak,
        down_n=down_n,
        min_level=min_level,
        max_level=max_level,
    )


def student_plot_staircase(history: list[dict], threshold: float, y_label: str, title: str) -> None:
    """Delegate to the shared 3AFC implementation."""
    shared_student_plot_staircase(
        history=history,
        threshold=threshold,
        y_label=y_label,
        title=title,
    )


def student_build_three_interval_targets(*, target_index: int) -> list[bool]:
    """Delegate to the shared 3AFC implementation."""
    return shared_student_build_three_interval_targets(target_index=target_index)


def student_update_staircase_state(
    *,
    current_level: float,
    step: float,
    is_correct: bool,
    correct_streak: int,
    down_n: int,
    min_level: float,
    max_level: float,
) -> tuple[float, int]:
    """Delegate to the shared 3AFC implementation."""
    return shared_student_update_staircase_state(
        current_level=current_level,
        step=step,
        is_correct=is_correct,
        correct_streak=correct_streak,
        down_n=down_n,
        min_level=min_level,
        max_level=max_level,
    )


def student_estimate_threshold_from_reversals(
    *, reversals: list[float], fallback_level: float, tail_count: int = 4
) -> float:
    """Delegate to the shared 3AFC implementation."""
    return shared_student_estimate_threshold_from_reversals(
        reversals=reversals,
        fallback_level=fallback_level,
        tail_count=tail_count,
    )


def student_compute_recent_accuracy(history: list[dict], window: int = 12) -> float:
    """Delegate to the shared 3AFC implementation."""
    return shared_student_compute_recent_accuracy(history=history, window=window)


def student_validate_audio_params(*, amplitude: float, frequency_hz: int) -> bool:
    """Delegate to the shared 3AFC implementation."""
    return shared_student_validate_audio_params(
        amplitude=amplitude,
        stimulus_value=float(frequency_hz),
    )


def student_plot_staircase_with_threshold(
    *, history: list[dict], threshold: float, y_label: str, title: str
) -> None:
    """Delegate to the shared 3AFC implementation."""
    shared_student_plot_staircase_with_threshold(
        history=history,
        threshold=threshold,
        y_label=y_label,
        title=title,
    )



adaptive = init_adaptive_state(
    "amplitude",
    start_level=float(cfg["adaptive"]["start_level"]),
    min_level=float(cfg["adaptive"]["min_level"]),
    max_level=float(cfg["adaptive"]["max_level"]),
    initial_step=float(cfg["adaptive"]["initial_step"]),
    min_step=float(cfg["adaptive"]["min_step"]),
    max_reversals=int(cfg["adaptive"]["max_reversals"]),
    down=int(cfg["adaptive"]["down"]),
)
trial = get_or_create_trial("amplitude")
current_delta_db = float(adaptive["current_level"])
feedback_key = "amplitude_last_feedback"

with st.container(border=True):
    st.subheader("3AFC Trial")
    baseline_amplitude = REFERENCE_AMPLITUDE
    reference_hz = REFERENCE_FREQUENCY_HZ
    ratio = 10 ** (current_delta_db / 20.0)
    target_amplitude = baseline_amplitude * ratio
    setup_col_1, setup_col_2 = st.columns(2)
    setup_col_1.metric("Fixed Reference Frequency", f"{reference_hz} Hz")
    setup_col_2.metric("Fixed Reference Amplitude", f"{baseline_amplitude:.2f}")
    st.caption(
        f"Current adaptive delta: {current_delta_db:.2f} dB | "
        f"Target amplitude: {target_amplitude:.4f} | Duration: {TONE_DURATION_S:.1f} s | "
        f"Reversals: {len(adaptive['reversals'])}/{adaptive['max_reversals']}"
    )

    if not student_validate_audio_params(
        amplitude=baseline_amplitude,
        frequency_hz=reference_hz,
    ):
        st.error("Playback frequency or reference amplitude is outside the safe range.")
        st.stop()
    trial_audio = student_build_amplitude_intervals_audio(
        baseline_amplitude=baseline_amplitude,
        delta_db=current_delta_db,
        reference_hz=reference_hz,
        target_index=int(trial["target_index"]),
    )
    if len(trial_audio) != 3:
        st.error("The trial must contain exactly three audio intervals.")
        st.stop()
    play_cols = st.columns(3)
    for idx, wav_bytes in enumerate(trial_audio):
        play_cols[idx].audio(wav_bytes, format="audio/wav")
        play_cols[idx].caption(f"Interval {idx + 1}")

with st.container(border=True):
    st.subheader("Respond")
    render_feedback(feedback_key)
    choice = st.radio("Which interval was louder?", [1, 2, 3], horizontal=True, key="amp_choice")
    submitted = st.button(
        "Submit Response",
        type="primary",
        width="stretch",
        disabled=adaptive["finished"],
    )
    if submitted and not adaptive["finished"]:
        submit_3afc_response(
            state_key="amplitude",
            adaptive=adaptive,
            trial=trial,
            level_used=current_delta_db,
            selected_interval=int(choice),
            feedback_key=feedback_key,
        )

    estimated_db = estimate_threshold(adaptive)
    history = adaptive["history"]
    col_1, col_2 = st.columns(2)
    col_1.metric("Estimated Threshold (dB)", f"{estimated_db:.2f}")
    with col_2:
        render_recent_accuracy_metric(history)

if adaptive["finished"]:
    with st.container(border=True):
        st.subheader("Test Complete")
        st.success("Staircase finished. Final estimate and statistics are shown below.")
        history = adaptive["history"]
        st.metric("Final Amplitude-Difference Threshold", f"{estimated_db:.2f} dB")
        render_completion_summary(adaptive, estimated_value=estimated_db, value_label="dB")
        st.caption("Final threshold is the mean of reversal points 3–6.")
        st.dataframe(
            [
                {"Reversal": index, "Amplitude Difference (dB)": float(value)}
                for index, value in enumerate(adaptive["reversals"], start=1)
            ],
            width="stretch",
            hide_index=True,
        )
        student_plot_staircase_with_threshold(
            history=history,
            threshold=estimated_db,
            y_label="Amplitude Delta (dB)",
            title="Amplitude Discrimination Adaptive Staircase",
        )
        st.subheader("Engineering and Human-Factors Interpretation")
        st.write(
            "Amplitude thresholds inform sensible volume-control increments and the "
            "salience of warning sounds. Accessible workplace and environmental audio "
            "should use comfortably distinguishable level changes, avoid unsafe loudness, "
            "and not treat this individual measurement as a clinical norm."
        )
        st.caption(
            "For the assignment report, document the session's auditory condition "
            "(unaided, hearing aid/assistive device, or other) without recording a diagnosis."
        )

with st.container(border=True):
    st.subheader("Test Controls")
    if st.button("Restart Test", width="stretch"):
        reset_adaptive_state("amplitude")
        st.session_state.pop(feedback_key, None)
        st.rerun()
