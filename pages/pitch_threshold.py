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
    page_title="Pitch Discrimination Threshold Test",
    layout="wide",
)

render_page_header(
    "Pitch Discrimination Threshold Test",
    "3AFC adaptive test: identify the interval with higher pitch.",
    "pitch_threshold",
)

render_instructions(
    "How To Run This Test",
    (
        "You will hear three tones at the same level. One tone has a slightly higher "
        "frequency than the reference. Select that interval each trial."
    ),
    [
        "This educational activity is not a medical diagnostic test.",
        (
            "Begin at a comfortable low volume. Stop immediately if any sound "
            "becomes uncomfortable."
        ),
        "Keep volume fixed throughout the test and use headphones if possible.",
        "Answer every trial even when unsure (forced choice).",
        "The adaptive staircase estimates your minimum detectable frequency increment.",
        "You may stop at any time by returning Home; responses stay in this local session.",
    ],
)

config = load_test_config()
cfg = config["pitch_discrimination"]
REFERENCE_FREQUENCY_HZ = int(cfg["reference_frequency_hz"]["default"])
TONE_DURATION_S = float(cfg["tone_duration_s"])
MAX_PLAYBACK_FREQUENCY_HZ = 20_000.0


def student_build_pitch_intervals_audio(
    *,
    reference_hz: int,
    delta_hz: float,
    amplitude: float,
    target_index: int,
) -> list[bytes]:
    """Build one 3AFC trial audio set for pitch discrimination.

    Why this function exists:
        Each trial requires three tones where only one differs in pitch. This helper
        keeps trial stimulus construction modular and testable.

    Inputs:
        reference_hz: Base frequency used for two non-target intervals.
        delta_hz: Positive pitch increment for the target interval.
        amplitude: Shared playback amplitude.
        target_index: Index (0, 1, 2) of the higher-pitch interval.

    Output:
        List of exactly 3 WAV byte payloads.

    Behavior:
        - Two clips at `reference_hz`.
        - One clip at `reference_hz + delta_hz`.
        - Keep duration and amplitude consistent across intervals.
    """
    try:
        safe_reference_hz = float(reference_hz)
        safe_delta_hz = float(delta_hz)
        safe_amplitude = float(amplitude)
    except (TypeError, ValueError) as error:
        raise ValueError("Pitch stimulus values must be numeric.") from error

    target_hz = safe_reference_hz + safe_delta_hz
    frequency_limits = cfg["reference_frequency_hz"]
    valid_reference = (
        float(frequency_limits["min"])
        <= safe_reference_hz
        <= float(frequency_limits["max"])
    )
    valid_duration = math.isfinite(TONE_DURATION_S) and 0.0 < TONE_DURATION_S <= 10.0
    if not (
        valid_reference
        and math.isfinite(safe_delta_hz)
        and safe_delta_hz > 0.0
        and target_hz <= MAX_PLAYBACK_FREQUENCY_HZ
        and valid_duration
        and shared_student_validate_audio_params(
            amplitude=safe_amplitude,
            stimulus_value=safe_reference_hz,
        )
    ):
        raise ValueError("Frequency, pitch difference, amplitude, or duration is unsafe.")

    target_mask = shared_student_build_three_interval_targets(target_index=target_index)
    reference_wav = single_tone_wav(
        frequency_hz=safe_reference_hz,
        duration_s=TONE_DURATION_S,
        amplitude=safe_amplitude,
    )
    target_wav = single_tone_wav(
        frequency_hz=target_hz,
        duration_s=TONE_DURATION_S,
        amplitude=safe_amplitude,
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


def student_validate_audio_params(*, amplitude: float, reference_hz: int) -> bool:
    """Delegate to the shared 3AFC implementation."""
    return shared_student_validate_audio_params(
        amplitude=amplitude,
        stimulus_value=float(reference_hz),
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
    "pitch_threshold",
    start_level=float(cfg["adaptive"]["start_level"]),
    min_level=float(cfg["adaptive"]["min_level"]),
    max_level=float(cfg["adaptive"]["max_level"]),
    initial_step=float(cfg["adaptive"]["initial_step"]),
    min_step=float(cfg["adaptive"]["min_step"]),
    max_reversals=int(cfg["adaptive"]["max_reversals"]),
    down=int(cfg["adaptive"]["down"]),
)
trial = get_or_create_trial("pitch_threshold")
current_delta_hz = float(adaptive["current_level"])
feedback_key = "pitch_threshold_last_feedback"

with st.container(border=True):
    st.subheader("3AFC Trial")
    reference_hz = REFERENCE_FREQUENCY_HZ
    st.metric("Fixed Reference Frequency", f"{reference_hz} Hz")
    amplitude = st.slider(
        "Playback amplitude",
        min_value=float(cfg["playback_amplitude"]["min"]),
        max_value=float(cfg["playback_amplitude"]["max"]),
        value=float(cfg["playback_amplitude"]["default"]),
        step=float(cfg["playback_amplitude"]["step"]),
        key="pitch_threshold_amplitude",
        disabled=bool(adaptive["history"]),
    )
    if adaptive["history"]:
        st.caption(
            "Playback amplitude is locked for this adaptive run. Keep system/device "
            "volume fixed until the run is complete."
        )
    else:
        st.caption(
            "Choose a comfortable low amplitude before starting, then keep system/device "
            "volume fixed throughout the run."
        )
    target_hz = float(reference_hz) + current_delta_hz
    st.caption(
        f"Current adaptive pitch delta: {current_delta_hz:.1f} Hz | "
        f"Target frequency: {target_hz:.1f} Hz | Duration: {TONE_DURATION_S:.1f} s"
    )
    st.caption(f"Reversals: {len(adaptive['reversals'])}/{adaptive['max_reversals']}")

    if not student_validate_audio_params(amplitude=amplitude, reference_hz=reference_hz):
        st.error("Playback frequency or amplitude is outside the safe configured range.")
        st.stop()
    trial_audio = student_build_pitch_intervals_audio(
        reference_hz=reference_hz,
        delta_hz=current_delta_hz,
        amplitude=amplitude,
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
    choice = st.radio("Which interval had the higher pitch?", [1, 2, 3], horizontal=True)
    submitted = st.button(
        "Submit Response",
        type="primary",
        width="stretch",
        disabled=adaptive["finished"],
    )
    if submitted and not adaptive["finished"]:
        submit_3afc_response(
            state_key="pitch_threshold",
            adaptive=adaptive,
            trial=trial,
            level_used=current_delta_hz,
            selected_interval=int(choice),
            feedback_key=feedback_key,
        )

    estimated_hz = estimate_threshold(adaptive)
    history = adaptive["history"]
    col_1, col_2 = st.columns(2)
    col_1.metric("Estimated Delta Threshold (Hz)", f"{estimated_hz:.1f}")
    with col_2:
        render_recent_accuracy_metric(history)

if adaptive["finished"]:
    with st.container(border=True):
        st.subheader("Test Complete")
        st.success("Staircase finished. Final estimate and statistics are shown below.")
        history = adaptive["history"]
        st.metric("Final Pitch-Difference Threshold", f"{estimated_hz:.1f} Hz")
        render_completion_summary(adaptive, estimated_value=estimated_hz, value_label="Hz")
        st.caption("Final threshold is the mean of reversal points 3–6.")
        st.dataframe(
            [
                {"Reversal": index, "Pitch Difference (Hz)": float(value)}
                for index, value in enumerate(adaptive["reversals"], start=1)
            ],
            width="stretch",
            hide_index=True,
        )
        student_plot_staircase_with_threshold(
            history=history,
            threshold=estimated_hz,
            y_label="Pitch Delta (Hz)",
            title="Pitch Discrimination Adaptive Staircase",
        )
        st.subheader("Engineering and Human-Factors Interpretation")
        st.write(
            "Pitch differences can distinguish auditory icons, alarms, notifications, "
            "and music or audio cues. Human-machine communication should use changes "
            "comfortably above this measured threshold and provide redundant cues for "
            "important information; this individual result is not a clinical norm."
        )
        st.caption(
            "For the assignment report, document the session's auditory condition "
            "(unaided, hearing aid/assistive device, or other) without recording a diagnosis."
        )

with st.container(border=True):
    st.subheader("Test Controls")
    if st.button("Restart Test", width="stretch"):
        reset_adaptive_state("pitch_threshold")
        st.session_state.pop(feedback_key, None)
        st.session_state.pop("pitch_threshold_amplitude", None)
        st.rerun()
