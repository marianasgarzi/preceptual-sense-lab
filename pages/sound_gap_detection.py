import io
import math
import wave

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
from utils.audio_tools import noise_burst_with_gap_wav
from utils.test_config import load_test_config
from utils.three_afc import (
    render_completion_summary,
    render_feedback,
    submit_3afc_response,
)
from utils.ui import (
    render_instructions,
    render_page_header,
)

st.set_page_config(
    page_title="Sound Gap Detection Test",
    layout="wide",
)

render_page_header(
    "Sound Gap Detection Test",
    "3AFC adaptive test: select which interval contains a silent gap.",
    "gap",
)

render_instructions(
    "How To Run This Test",
    (
        "You will hear three short noise bursts. Exactly one burst contains a "
        "centered silence gap. Pick the correct interval every trial."
    ),
    [
        "This is an educational activity, not a diagnostic or medical test.",
        (
            "Start at a low, comfortable volume. Stop immediately if any sound "
            "feels uncomfortable."
        ),
        "Use all three play buttons to compare candidates before answering.",
        "Select the interval with the gap, then submit your response.",
        "The adaptive staircase will shrink or expand the gap based on performance.",
        "You may stop at any time by returning Home; responses stay in this local session.",
    ],
)

config = load_test_config()
cfg = config["gap_detection"]
GAP_SAMPLE_RATE = 44_100


def delivered_gap_duration_ms(gap_ms: float, sample_rate: int = GAP_SAMPLE_RATE) -> float:
    """Return the sample-quantized gap duration that audio playback can deliver."""
    if not math.isfinite(float(gap_ms)) or float(gap_ms) < 0.0 or sample_rate <= 0:
        raise ValueError("Gap duration and sample rate must be valid.")
    gap_frames = round(float(gap_ms) * sample_rate / 1000.0)
    return gap_frames / sample_rate * 1000.0


def student_build_gap_intervals_audio(
    *,
    gap_ms: float,
    amplitude: float,
    target_index: int,
    seed: int,
) -> list[bytes]:
    """Build one 3AFC trial audio set for gap detection.

    Why this function exists:
        The listener must compare three intervals where only one contains the silent
        gap. Centralizing generation here makes stimuli reproducible and easy to test.

    Inputs:
        gap_ms: Gap duration for the target interval.
        amplitude: Playback amplitude for all intervals.
        target_index: Index (0, 1, 2) containing the gap.
        seed: Seed used so generated noise bursts are deterministic.

    Output:
        A list of exactly three WAV byte payloads.

    Behavior:
        - Target interval gets `gap_ms`.
        - Other intervals get zero gap.
        - Keep amplitude consistent across all three clips.
        - Use deterministic seeds so repeated runs are reproducible.
    """
    if not shared_student_validate_audio_params(
        amplitude=amplitude,
        stimulus_value=gap_ms,
    ):
        raise ValueError("Amplitude and gap duration must be finite and in safe ranges.")
    target_mask = shared_student_build_three_interval_targets(target_index=target_index)

    duration_s = float(cfg["playback"]["burst_duration_s"])
    continuous_wav = noise_burst_with_gap_wav(
        duration_s=duration_s,
        gap_ms=0.0,
        amplitude=float(amplitude),
        seed=int(seed),
        sample_rate=GAP_SAMPLE_RATE,
    )

    with wave.open(io.BytesIO(continuous_wav), "rb") as source:
        params = source.getparams()
        frames = bytearray(source.readframes(source.getnframes()))
        frame_count = source.getnframes()
        frame_width = source.getnchannels() * source.getsampwidth()
        gap_frames = min(
            frame_count,
            max(0, round(float(gap_ms) * source.getframerate() / 1000)),
        )

    gap_start = max(0, (frame_count - gap_frames) // 2)
    target_frames = frames.copy()
    byte_start = gap_start * frame_width
    byte_end = byte_start + gap_frames * frame_width
    target_frames[byte_start:byte_end] = b"\x00" * (byte_end - byte_start)

    target_buffer = io.BytesIO()
    with wave.open(target_buffer, "wb") as target_wav:
        target_wav.setparams(params)
        target_wav.writeframes(target_frames)
    target_wav_bytes = target_buffer.getvalue()

    return [target_wav_bytes if is_target else continuous_wav for is_target in target_mask]


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


def student_validate_audio_params(*, amplitude: float, gap_ms: float) -> bool:
    """Delegate to the shared 3AFC implementation."""
    return shared_student_validate_audio_params(amplitude=amplitude, stimulus_value=gap_ms)


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
    "gap",
    start_level=float(cfg["adaptive"]["start_level"]),
    min_level=float(cfg["adaptive"]["min_level"]),
    max_level=float(cfg["adaptive"]["max_level"]),
    initial_step=float(cfg["adaptive"]["initial_step"]),
    min_step=float(cfg["adaptive"]["min_step"]),
    max_reversals=int(cfg["adaptive"]["max_reversals"]),
    down=int(cfg["adaptive"]["down"]),
)
trial = get_or_create_trial("gap")
current_gap_ms = float(adaptive["current_level"])
feedback_key = "gap_last_feedback"

with st.container(border=True):
    st.subheader("3AFC Trial")
    amplitude = st.slider(
        "Playback amplitude",
        min_value=float(cfg["playback"]["amplitude"]["min"]),
        max_value=float(cfg["playback"]["amplitude"]["max"]),
        value=float(cfg["playback"]["amplitude"]["default"]),
        step=float(cfg["playback"]["amplitude"]["step"]),
        key="gap_amplitude",
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
    delivered_gap_ms = delivered_gap_duration_ms(current_gap_ms)
    st.caption(
        f"Requested adaptive gap: {current_gap_ms:.4f} ms | "
        f"Delivered gap: {delivered_gap_ms:.4f} ms | "
        f"Reversals: {len(adaptive['reversals'])}/{adaptive['max_reversals']}"
    )
    if not student_validate_audio_params(amplitude=amplitude, gap_ms=current_gap_ms):
        st.error("Playback parameters are invalid. Restart the test before continuing.")
        st.stop()
    trial_audio = student_build_gap_intervals_audio(
        gap_ms=current_gap_ms,
        amplitude=amplitude,
        target_index=int(trial["target_index"]),
        seed=int(trial["seed"]),
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
    choice = st.radio("Which interval had the gap?", [1, 2, 3], horizontal=True)
    submitted = st.button(
        "Submit Response",
        type="primary",
        width="stretch",
        disabled=adaptive["finished"],
    )
    if submitted and not adaptive["finished"]:
        submit_3afc_response(
            state_key="gap",
            adaptive=adaptive,
            trial=trial,
            level_used=delivered_gap_ms,
            selected_interval=int(choice),
            feedback_key=feedback_key,
        )

    estimated_gap = estimate_threshold(adaptive)
    st.metric("Estimated Gap Threshold (ms)", f"{estimated_gap:.2f}")

if adaptive["finished"]:
    with st.container(border=True):
        st.subheader("Test Complete")
        st.success("Staircase finished. Final estimate and statistics are shown below.")
        history = adaptive["history"]
        st.metric("Final Gap Threshold", f"{estimated_gap:.2f} ms")
        render_completion_summary(adaptive, estimated_value=estimated_gap, value_label="ms")
        st.caption("Final threshold is the mean of reversal points 3–6.")
        st.dataframe(
            [
                {"Reversal": index, "Delivered Gap (ms)": float(value)}
                for index, value in enumerate(adaptive["reversals"], start=1)
            ],
            width="stretch",
            hide_index=True,
        )
        student_plot_staircase_with_threshold(
            history=history,
            threshold=estimated_gap,
            y_label="Gap (ms)",
            title="Gap Detection Adaptive Staircase",
        )
        st.subheader("Engineering and Human-Factors Interpretation")
        st.write(
            "Gap detection reflects temporal resolution relevant to speech perception, "
            "auditory alerts, and time-critical feedback. Important signals should use "
            "timing differences comfortably above this measured threshold and should not "
            "treat an individual result as a clinical norm."
        )
        st.caption(
            "For the assignment report, document the session's auditory condition "
            "(unaided, hearing aid/assistive device, or other) without recording a diagnosis."
        )

with st.container(border=True):
    st.subheader("Test Controls")
    if st.button("Restart Test", width="stretch"):
        reset_adaptive_state("gap")
        st.session_state.pop(feedback_key, None)
        st.session_state.pop("gap_amplitude", None)
        st.rerun()
