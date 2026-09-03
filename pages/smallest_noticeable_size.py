import math
import random

import streamlit as st

from utils.test_config import load_test_config
from utils.ui import (
    render_instructions,
    render_page_header,
)

st.set_page_config(
    page_title="Visual Resolution (Tumbling E Staircase)",
    layout="wide",
)

render_page_header(
    "Visual Resolution Test (Tumbling E Staircase)",
    "Single-optotype adaptive staircase with error logging and MAR tracking.",
    "size",
)

render_instructions(
    "How To Run This Test",
    (
        "You will see one Tumbling E at a time. Choose its orientation. "
        "Correct responses make the next E smaller. The first incorrect response "
        "completes the test at the smallest size identified correctly."
    ),
    [
        "This educational activity is not a medical diagnostic test.",
        "Keep viewing distance fixed during the run.",
        "Keep your correction condition consistent if you use glasses or contacts.",
        "Answer every trial with one of: Up, Down, Left, Right.",
        "You may stop at any time by returning Home; responses stay in this local session.",
    ],
)

config = load_test_config()
cfg = config["tumbling_e"]
SIZE_LEVELS_PX = [int(v) for v in cfg["size_levels_px"]]
ORIENTATIONS = ["Up", "Down", "Left", "Right"]

if not SIZE_LEVELS_PX or min(SIZE_LEVELS_PX) < 5:
    st.error("The Tumbling-E schedule must use a minimum full-optotype size of 5 px.")
    st.stop()


def student_next_size_index(*, current_index: int, is_correct: bool, max_index: int) -> int:
    """Compute the next adaptive size index for the staircase.

    Why this function exists:
        This is the core adaptive rule for the visual acuity task. The page calls it
        after every response to decide whether the next Tumbling E should be harder
        (smaller) or easier (larger). If this logic is wrong, the whole test becomes
        invalid because stimulus difficulty no longer tracks performance.

    Inputs:
        current_index: Current index in `SIZE_LEVELS_PX`.
        is_correct: Whether the participant selected the correct orientation this trial.
        max_index: Largest valid index in the size-level list.

    Output:
        The next valid index (integer) in the closed range `[0, max_index]`.

    Behavior:
        - Correct response: move to a smaller optotype by increasing index by 1.
        - Incorrect response: move to a larger optotype by decreasing index by 1.
        - Always clamp so index never goes below 0 or above `max_index`.
    """
    safe_max_index = max(0, int(max_index))
    safe_index = max(0, min(int(current_index), safe_max_index))
    change = 1 if is_correct else -1
    return max(0, min(safe_max_index, safe_index + change))


def student_build_trial_log_row(
    *,
    trial_no: int,
    size_px: int,
    mar_arcmin: float,
    correct_orientation: str,
    response: str,
) -> dict[str, str | int | float]:
    """Build a complete, standardized row for the trial log table.

    Why this function exists:
        The experiment needs a clean row per trial for grading and analysis. This
        function converts raw trial values into the exact display schema used later
        by `st.dataframe`, so every row is consistent and easy to interpret.

    Inputs:
        trial_no: 1-based trial counter.
        size_px: Rendered optotype size (pixels) for this trial.
        mar_arcmin: Calculated MAR value for this size and setup.
        correct_orientation: Ground-truth direction shown to the participant.
        response: Participant-selected direction.

    Output:
        Dictionary with the exact table columns expected by this page, including a
        correctness field derived from `response == correct_orientation`.

    Behavior:
        - Keep column names consistent with existing table rendering.
        - Include correctness as an explicit readable value.
        - Round MAR to 2 decimals for stable, readable output.
    """
    critical_feature_px = float(size_px) / 5.0
    return {
        "Trial": max(1, int(trial_no)),
        "E Orientation": str(correct_orientation),
        "Full E Size (px)": int(size_px),
        "Critical Feature (px)": round(critical_feature_px, 2),
        "Participant Response": str(response),
        "Correct": "Yes" if response == correct_orientation else "No",
        "Angular Resolution (arcmin)": round(float(mar_arcmin), 2),
    }


def student_validate_screen_geometry(
    *, distance_cm: float, screen_width_mm: float, screen_width_px: int
) -> bool:
    """Validate whether screen-geometry inputs are usable.

    Why this function exists:
        MAR calculations rely on physically meaningful geometry values. Invalid
        distances or screen dimensions create nonsense results and confuse users.

    Inputs:
        distance_cm: Viewing distance in centimeters.
        screen_width_mm: Physical display width in millimeters.
        screen_width_px: Horizontal pixel resolution corresponding to width.

    Output:
        `True` when values are valid for computation; otherwise `False`.

    Validation:
        - All values are positive.
        - Pixel width is large enough to avoid divide-by-zero / tiny denominator.
        - Distance and width remain in realistic human-testing ranges.
    """
    try:
        safe_distance = float(distance_cm)
        safe_width_mm = float(screen_width_mm)
        safe_width_px = int(screen_width_px)
    except (TypeError, ValueError):
        return False
    setup = cfg["setup"]
    return (
        math.isfinite(safe_distance)
        and math.isfinite(safe_width_mm)
        and float(setup["distance_cm"]["min"])
        <= safe_distance
        <= float(setup["distance_cm"]["max"])
        and float(setup["screen_width_mm"]["min"])
        <= safe_width_mm
        <= float(setup["screen_width_mm"]["max"])
        and int(setup["screen_width_px"]["min"])
        <= safe_width_px
        <= int(setup["screen_width_px"]["max"])
    )


def student_compute_mar_arcmin(size_px: int, mm_per_px: float, distance_cm: float) -> float:
    """Compute MAR (minimum angle of resolution) in arcminutes.

    Why this function exists:
        Pixel size alone is device-dependent; MAR converts that size into a vision
        metric that is comparable across screens and viewing distances.

    Inputs:
        size_px: Current optotype size in pixels.
        mm_per_px: Pixel pitch (millimeters per pixel).
        distance_cm: Viewing distance in centimeters.

    Output:
        MAR in arcminutes as a float.

    Calculation:
        - Convert pixel size to millimeters (`size_px * mm_per_px`).
        - Convert distance to matching units (millimeters).
        - Use a small-angle geometry formula, then convert radians to arcminutes.
        - Return a positive float and guard invalid denominators.
    """
    try:
        safe_size_px = float(size_px)
        safe_mm_per_px = float(mm_per_px)
        safe_distance_cm = float(distance_cm)
    except (TypeError, ValueError):
        return 0.0
    if not (
        math.isfinite(safe_size_px)
        and math.isfinite(safe_mm_per_px)
        and math.isfinite(safe_distance_cm)
        and safe_size_px > 0.0
        and safe_mm_per_px > 0.0
        and safe_distance_cm > 0.0
    ):
        return 0.0
    critical_feature_mm = (safe_size_px / 5.0) * safe_mm_per_px
    distance_mm = safe_distance_cm * 10.0
    angle_radians = 2.0 * math.atan(critical_feature_mm / (2.0 * distance_mm))
    return angle_radians * (180.0 / math.pi) * 60.0


def student_format_trial_log_row(
    *,
    trial_no: int,
    size_px: int,
    mar_arcmin: float,
    correct_orientation: str,
    response: str,
) -> dict[str, str | int | float]:
    """Wrapper/formatter for a standardized trial-log row.

    Why this function exists:
        In many real codebases, one helper computes values and another helper
        formats them for display. Keeping this function separate teaches modular
        design and avoids spreading table-format logic across the page.

    Behavior:
        This function should return the same schema as `student_build_trial_log_row`,
        potentially by calling it internally and applying final formatting rules.
    """
    return student_build_trial_log_row(
        trial_no=trial_no,
        size_px=size_px,
        mar_arcmin=mar_arcmin,
        correct_orientation=correct_orientation,
        response=response,
    )



if not student_validate_screen_geometry(
    distance_cm=float(cfg["setup"]["distance_cm"]["default"]),
    screen_width_mm=float(cfg["setup"]["screen_width_mm"]["default"]),
    screen_width_px=int(cfg["setup"]["screen_width_px"]["default"]),
):
    st.error("Geometry validation function returned invalid result.")
    st.stop()


def init_tumbling_state() -> dict:
    key = "tumbling_e_state"
    if key not in st.session_state:
        st.session_state[key] = {
            "size_index": 0,
            "trial_orientation": random.choice(ORIENTATIONS),
            "history": [],
            "finished": False,
            "threshold_size_px": None,
            "completion_reason": None,
        }
    return st.session_state[key]


def next_orientation(previous: str) -> str:
    candidate = random.choice(ORIENTATIONS)
    while candidate == previous:
        candidate = random.choice(ORIENTATIONS)
    return candidate


def e_symbol(size_px: int, orientation: str) -> str:
    rotation = {"Right": 0, "Down": 90, "Left": 180, "Up": 270}[orientation]
    return (
        "<div style='display:flex; justify-content:center; align-items:center; "
        "background:#ffffff; border:1px solid #d0d0d0; border-radius:8px; padding:0.3rem;'>"
        # LAB NOTE: SVG geometry enforces t=d (stroke thickness equals spacing) on a 5x5 grid.
        f"<svg width='{size_px}' height='{size_px}' viewBox='0 0 5 5' "
        "xmlns='http://www.w3.org/2000/svg' style='display:block; shape-rendering:crispEdges;'>"
        f"<g transform='rotate({rotation} 2.5 2.5)' fill='#101010'>"
        "<rect x='0' y='0' width='1' height='5'/>"
        "<rect x='0' y='0' width='5' height='1'/>"
        "<rect x='0' y='2' width='5' height='1'/>"
        "<rect x='0' y='4' width='5' height='1'/>"
        "</g></svg></div>"
    )


state = init_tumbling_state()
setup_locked = bool(state["history"])

with st.container(border=True):
    st.subheader("Test Setup")
    col_1, col_2, col_3 = st.columns(3)
    distance_cm = col_1.number_input(
        "Viewing distance (cm)",
        min_value=float(cfg["setup"]["distance_cm"]["min"]),
        max_value=float(cfg["setup"]["distance_cm"]["max"]),
        value=float(cfg["setup"]["distance_cm"]["default"]),
        step=float(cfg["setup"]["distance_cm"]["step"]),
        disabled=setup_locked,
    )
    screen_width_mm = col_2.number_input(
        "Screen width (mm)",
        min_value=float(cfg["setup"]["screen_width_mm"]["min"]),
        max_value=float(cfg["setup"]["screen_width_mm"]["max"]),
        value=float(cfg["setup"]["screen_width_mm"]["default"]),
        step=float(cfg["setup"]["screen_width_mm"]["step"]),
        disabled=setup_locked,
    )
    screen_width_px = col_3.number_input(
        "Screen width (pixels)",
        min_value=int(cfg["setup"]["screen_width_px"]["min"]),
        max_value=int(cfg["setup"]["screen_width_px"]["max"]),
        value=int(cfg["setup"]["screen_width_px"]["default"]),
        step=int(cfg["setup"]["screen_width_px"]["step"]),
        disabled=setup_locked,
    )
    if not student_validate_screen_geometry(
        distance_cm=distance_cm,
        screen_width_mm=screen_width_mm,
        screen_width_px=screen_width_px,
    ):
        st.error("Screen geometry is outside the valid configured ranges.")
        st.stop()
    mm_per_px = float(screen_width_mm) / float(screen_width_px)
    st.caption(f"Pixel pitch: {mm_per_px:.4f} mm/px")
    st.caption("Geometry assumes square display pixels, so horizontal pitch applies vertically.")
    st.caption(
        f"The configured E schedule ranges from {SIZE_LEVELS_PX[0]} px to "
        f"{SIZE_LEVELS_PX[-1]} px. Its critical stroke/gap width is always one-fifth "
        "of the full optotype size."
    )


def mar_arcmin_for_size(size_px: int, mm_per_px: float, distance_cm: float) -> float:
    return student_compute_mar_arcmin(size_px=size_px, mm_per_px=mm_per_px, distance_cm=distance_cm)


feedback_key = "tumbling_e_last_feedback"
current_index = int(state["size_index"])
current_size_px = SIZE_LEVELS_PX[current_index]
current_orientation = state["trial_orientation"]
current_mar = mar_arcmin_for_size(current_size_px, mm_per_px, distance_cm)
finished = bool(state["finished"])

with st.container(border=True):
    st.subheader("Adaptive Tumbling E Trial")
    current_critical_px = current_size_px / 5.0
    st.caption(
        f"Full E size: {current_size_px}px | Critical stroke/gap: "
        f"{current_critical_px:.2f}px | Current angular resolution: "
        f"{current_mar:.2f} arcmin"
    )
    st.markdown(e_symbol(current_size_px, current_orientation), unsafe_allow_html=True)

with st.container(border=True):
    st.subheader("Respond")
    last_feedback = st.session_state.get(feedback_key)
    if last_feedback == "correct":
        st.success("Previous response: Correct.")
    elif last_feedback == "incorrect":
        st.error("Previous response: Incorrect.")

    response = st.radio("Orientation", ORIENTATIONS, horizontal=True, disabled=finished)
    submitted = st.button(
        "Submit Response",
        type="primary",
        width="stretch",
        disabled=finished,
    )
    if submitted and not finished:
        is_correct = response == current_orientation
        next_index = student_next_size_index(
            current_index=current_index,
            is_correct=is_correct,
            max_index=len(SIZE_LEVELS_PX) - 1,
        )
        state["history"].append(
            student_format_trial_log_row(
                trial_no=len(state["history"]) + 1,
                size_px=current_size_px,
                mar_arcmin=current_mar,
                correct_orientation=current_orientation,
                response=response,
            )
        )

        if is_correct:
            state["threshold_size_px"] = current_size_px
            if current_index >= len(SIZE_LEVELS_PX) - 1:
                state["finished"] = True
                state["completion_reason"] = "smallest_level_correct"
            else:
                state["size_index"] = next_index
                state["trial_orientation"] = next_orientation(current_orientation)
        else:
            state["finished"] = True
            state["completion_reason"] = "incorrect_response"
        st.session_state[feedback_key] = "correct" if is_correct else "incorrect"
        st.rerun()

with st.container(border=True):
    st.subheader("Results")
    threshold_size_value = state["threshold_size_px"]
    if not finished:
        if threshold_size_value is None:
            st.caption("Test in progress. No provisional threshold is available yet.")
        else:
            st.metric("Provisional Smallest Correct Full E Size", f"{threshold_size_value} px")
            st.caption("This is an in-progress value, not a final result.")
    elif threshold_size_value is None:
        st.subheader("Test Complete")
        st.warning(
            "The first E orientation was not identified correctly, so a threshold "
            "was not established within the tested range."
        )
        st.caption(
            "For the assignment report, document the session's visual condition "
            "(unaided, glasses, contacts, or other) without recording a diagnosis."
        )
    else:
        st.subheader("Test Complete")
        threshold_size_px = int(threshold_size_value)
        critical_feature_px = threshold_size_px / 5.0
        critical_feature_mm = critical_feature_px * mm_per_px
        threshold_arcmin = student_compute_mar_arcmin(
            size_px=threshold_size_px,
            mm_per_px=mm_per_px,
            distance_cm=distance_cm,
        )
        st.success("Tumbling-E run complete.")
        result_col_1, result_col_2, result_col_3, result_col_4 = st.columns(4)
        result_col_1.metric("Smallest Correct Full E", f"{threshold_size_px} px")
        result_col_2.metric("Critical Feature Width", f"{critical_feature_px:.2f} px")
        result_col_3.metric("Physical Critical Width", f"{critical_feature_mm:.4f} mm")
        result_col_4.metric("Angular Resolution", f"{threshold_arcmin:.2f} arcmin")

        if state["completion_reason"] == "incorrect_response":
            st.caption(
                "The threshold is the smallest correctly identified size immediately "
                "before the first incorrect response."
            )
        else:
            st.caption(
                "The participant reached the display-limited 5 px lower bound. At this "
                "size, each unit of the 5×5 E is one physical display pixel; a finer "
                "threshold cannot be measured reliably with the current pixel geometry."
            )

        st.subheader("Geometry Used")
        st.markdown(
            "- Pixel pitch: `screen width (mm) / horizontal resolution (px)`\n"
            "- Critical feature: `full E size (px) / 5`\n"
            "- Critical width: `critical feature (px) × pixel pitch (mm/px)`\n"
            "- Exact angle: `θ = 2 × atan(critical width / (2 × viewing distance))`\n"
            "- Angular resolution: `θ × 180/π × 60` arcminutes"
        )
        st.caption(
            "The 5×5 SVG preserves equal stroke and gap units. The test stops at a 5 px "
            "full E so its one-unit critical feature is never rendered below one display pixel."
        )

        st.subheader("Display and Readability Interpretation")
        st.write(
            "This critical-feature threshold helps estimate whether text strokes, icon details, "
            "and warning symbols remain resolvable at the tested distance. Important display "
            "elements should use features comfortably larger than this boundary. Longer viewing "
            "distances increase the required physical feature size, so display design should "
            "account for expected distance, pixel density, and the visibility needs of users."
        )
        st.caption(
            "For the assignment report, document the session's visual condition "
            "(unaided, glasses, contacts, or other) without recording a diagnosis."
        )

with st.container(border=True):
    st.subheader("Trial Log")
    history = state["history"]
    if history:
        st.dataframe(history, width="stretch", hide_index=True)
        wrong_only = [row for row in history if row["Correct"] == "No"]
        st.markdown("**Incorrect Responses**")
        if wrong_only:
            st.dataframe(wrong_only, width="stretch", hide_index=True)
        else:
            st.caption("No incorrect responses yet.")
    else:
        st.caption("No responses yet.")

with st.container(border=True):
    st.subheader("Test Controls")
    if st.button("Restart Test", width="stretch"):
        st.session_state.pop("tumbling_e_state", None)
        st.session_state.pop(feedback_key, None)
        st.rerun()
