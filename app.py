import streamlit as st

st.set_page_config(page_title="Perceptual Sense Lab", layout="wide")

st.title("Human Sensory Thresholds — Perceptual Sense Lab")
st.write(
    "Explore six short experiments that estimate visual and auditory thresholds "
    "under your current viewing, listening, equipment, and environmental conditions."
)

st.info(
    "Educational use only. This application is not medically validated and is not a "
    "diagnostic test. You may stop participating at any time. Results remain in this "
    "local Streamlit session and are not uploaded or permanently stored."
)

st.subheader("Choose an experiment")

experiments = [
    ("Contrast Sensitivity", "pages/greyscale_resolution.py"),
    ("Smallest Noticeable Size", "pages/smallest_noticeable_size.py"),
    ("Pitch Frequency Range", "pages/pitch_frequency_range.py"),
    ("Sound Gap Detection", "pages/sound_gap_detection.py"),
    ("Pitch Difference Threshold", "pages/pitch_threshold.py"),
    ("Amplitude Difference Threshold", "pages/amplitude_threshold.py"),
]

left, right = st.columns(2)
for index, (label, page) in enumerate(experiments):
    container = left if index % 2 == 0 else right
    with container:
        st.page_link(page, label=label, icon="🧪")
