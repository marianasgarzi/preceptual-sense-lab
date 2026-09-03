import math

import streamlit as st

from utils.audio_tools import single_tone_wav
from utils.test_config import load_test_config
from utils.ui import (
    render_instructions,
    render_page_header,
)

st.set_page_config(
    page_title="Pitch Frequency Range Test",
    layout="wide",
)

render_page_header(
    "Pitch Frequency Range Test",
    "Use fine-grained controls to find your audible frequency range between 20 Hz and 20 kHz.",
    "pitch",
)

render_instructions(
    "How To Run This Test",
    (
        "Test tones from low to high frequencies with small frequency steps. Keep "
        "system volume fixed and use a quiet environment."
    ),
    [
        "This educational activity is not a medical diagnostic test.",
        "Begin at a low, comfortable system volume and keep it fixed throughout the test.",
        "Do not increase volume to force audibility at high frequencies.",
        "Stop immediately if any sound becomes uncomfortable.",
        "Choose a frequency, play it, and record whether it was clearly heard.",
        "You may stop at any time by returning Home or selecting Finish Test.",
    ],
)

config = load_test_config()
cfg = config["pitch_range"]
TONE_DURATION_S = 1.0
FREQUENCY_STEP_HZ = 50
MAX_PROBES = 100


def format_frequency_hz(frequency_hz: int) -> str:
    """Format frequency as Hz under 1 kHz and kHz above 1 kHz."""
    if frequency_hz < 1000:
        return f"{frequency_hz} Hz"
    return f"{frequency_hz / 1000:.2f} kHz"


default_frequency = int(cfg["frequency_hz"]["default"])
default_amplitude = float(cfg["playback_amplitude"]["default"])


def student_estimate_audible_bounds(
    *,
    probe_history_hz: list[int],
    heard_flags: list[bool],
) -> tuple[int, int]:
    """summarize heard probe frequencies into lower/upper bounds.

    Pair the frequencies marked as heard and return the min/max. If no probes
    were heard, return a sensible fallback such as the configured default.
    """
    heard_frequencies = []
    for frequency, heard in zip(probe_history_hz, heard_flags, strict=False):
        try:
            safe_frequency = int(frequency)
        except (TypeError, ValueError):
            continue
        if heard and student_validate_audio_params(
            frequency_hz=safe_frequency,
            amplitude=default_amplitude,
        ):
            heard_frequencies.append(safe_frequency)
    if not heard_frequencies:
        return 0, 0
    return min(heard_frequencies), max(heard_frequencies)


def student_validate_audio_params(*, frequency_hz: int, amplitude: float) -> bool:
    """ensure requested playback parameters stay within config limits.

    Return `True` when `frequency_hz` and `amplitude` fall inside the configured
    range, otherwise return `False`.
    """
    try:
        safe_frequency = int(frequency_hz)
        safe_amplitude = float(amplitude)
    except (TypeError, ValueError):
        return False
    frequency_config = cfg["frequency_hz"]
    amplitude_config = cfg["playback_amplitude"]
    return (
        math.isfinite(safe_amplitude)
        and int(frequency_config["min"])
        <= safe_frequency
        <= int(frequency_config["max"])
        and float(amplitude_config["min"])
        <= safe_amplitude
        <= float(amplitude_config["max"])
    )


with st.expander("Test Method"):
    st.markdown(
        "- Probe tones manually between 20 Hz and 20,000 Hz.\n"
        "- Record whether each tone was clearly heard.\n"
        "- Finish explicitly; the highest audible probe becomes the estimated upper bound."
    )

st.caption(
    "Consumer speakers and headphones may not reproduce the full 20 Hz–20 kHz range "
    "accurately. A missed low or high tone may reflect playback hardware, browser, or "
    "environment limitations rather than hearing alone."
)

if "pitch_range_state" not in st.session_state:
    st.session_state["pitch_range_state"] = {"history": [], "finished": False}
state = st.session_state["pitch_range_state"]
history = state["history"]
finished = bool(state["finished"])

with st.container(border=True):
    st.subheader("Tone Playback")
    frequency_hz = st.number_input(
        "Exact test frequency (Hz)",
        min_value=int(cfg["frequency_hz"]["min"]),
        max_value=int(cfg["frequency_hz"]["max"]),
        value=default_frequency,
        step=FREQUENCY_STEP_HZ,
        key="pitch_playback_input",
        disabled=finished,
    )
    amplitude = st.slider(
        "Playback amplitude",
        min_value=float(cfg["playback_amplitude"]["min"]),
        max_value=float(cfg["playback_amplitude"]["max"]),
        value=default_amplitude,
        step=float(cfg["playback_amplitude"]["step"]),
        key="pitch_range_amplitude",
        disabled=bool(history) or finished,
    )
    valid_duration = math.isfinite(TONE_DURATION_S) and 0.0 < TONE_DURATION_S <= 5.0
    valid_audio = student_validate_audio_params(
        frequency_hz=int(frequency_hz),
        amplitude=float(amplitude),
    ) and valid_duration
    if not valid_audio:
        st.error("Frequency, amplitude, or duration is outside the safe configured range.")
        st.stop()
    if not finished:
        st.audio(
            single_tone_wav(
                frequency_hz=float(frequency_hz),
                duration_s=TONE_DURATION_S,
                amplitude=float(amplitude),
            ),
            format="audio/wav",
        )
    st.caption(
        f"Current test tone: {format_frequency_hz(int(frequency_hz))} | "
        f"Duration: {TONE_DURATION_S:.1f} s"
    )

with st.container(border=True):
    st.subheader("Record Probe")
    heard_response = st.radio(
        "Was this tone clearly audible?",
        ["Heard", "Not heard"],
        horizontal=True,
        disabled=finished,
    )
    record_col, finish_col = st.columns(2)
    record_probe = record_col.button(
        "Record Probe",
        type="primary",
        width="stretch",
        disabled=finished or len(history) >= MAX_PROBES,
    )
    finish_test = finish_col.button(
        "Finish Test",
        width="stretch",
        disabled=finished,
    )
    if record_probe and not finished:
        history.append(
            {
                "Probe": len(history) + 1,
                "Frequency (Hz)": int(frequency_hz),
                "Heard": "Yes" if heard_response == "Heard" else "No",
            }
        )
        if len(history) >= MAX_PROBES:
            state["finished"] = True
        st.rerun()
    if finish_test and not finished:
        state["finished"] = True
        st.rerun()

heard_frequencies = [int(row["Frequency (Hz)"]) for row in history if row["Heard"] == "Yes"]
with st.container(border=True):
    st.subheader("Probe Summary")
    if heard_frequencies:
        st.metric("Highest Clearly Audible So Far", f"{max(heard_frequencies)} Hz")
    else:
        st.subheader("Test Complete")
        st.caption("No frequency has been recorded as clearly audible.")
    if history:
        st.dataframe(history, width="stretch", hide_index=True)
    else:
        st.caption("No probes recorded yet.")

with st.container(border=True):
    st.subheader("Final Result")
    if not finished:
        st.caption("Test in progress. Select Finish Test when you have enough probes.")
    elif not heard_frequencies:
        st.subheader("Test Complete")
        st.warning(
            "No tested frequency was marked clearly audible, so an upper audible-frequency "
            "bound was not established."
        )
        st.caption(
            "For the assignment report, document the session's auditory condition "
            "(unaided, hearing aid/assistive device, or other) without recording a diagnosis."
        )
    else:
        lower_hz, upper_hz = student_estimate_audible_bounds(
            probe_history_hz=[int(row["Frequency (Hz)"]) for row in history],
            heard_flags=[row["Heard"] == "Yes" for row in history],
        )
        st.success("Pitch-frequency range test complete.")
        result_col_1, result_col_2 = st.columns(2)
        result_col_1.metric("Lowest Recorded Audible Probe", f"{lower_hz} Hz")
        result_col_2.metric("Estimated Upper Audible Bound", f"{upper_hz} Hz")
        st.write(
            "This is the highest tested frequency marked clearly audible under the current "
            "equipment, browser, volume, and environmental conditions. It is an estimate, "
            "not a clinical hearing limit."
        )
        st.write(
            "Alarm and notification sounds should not rely only on very high-frequency cues. "
            "Auditory interfaces should accommodate age and user variability, provide broader "
            "or redundant cues for accessibility, and account for hardware playback limits when "
            "communicating critical information."
        )
        st.caption(
            "For the assignment report, document the session's auditory condition "
            "(unaided, hearing aid/assistive device, or other) without recording a diagnosis."
        )

with st.container(border=True):
    st.subheader("Test Controls")
    if st.button("Restart Test", width="stretch"):
        for key in [
            "pitch_range_state",
            "pitch_playback_input",
            "pitch_range_amplitude",
        ]:
            st.session_state.pop(key, None)
        st.rerun()
