# Perceptual Sense Lab

Perceptual Sense Lab is a Streamlit application for a Human Sensory Thresholds course
assignment. It provides six educational experiments for exploring visual and auditory
thresholds under the participant's current equipment and environmental conditions.

The application includes:

- Contrast Sensitivity: identifies letters across decreasing contrast levels.
- Smallest Noticeable Size: resolves the orientation of a 5×5 Tumbling E and reports
  angular resolution in arcminutes.
- Pitch Frequency Range: records heard/not-heard probes from 20 Hz to 20,000 Hz.
- Sound Gap Detection: estimates the shortest detected silent gap in noise.
- Pitch Difference Threshold: estimates a detectable frequency difference in hertz.
- Amplitude Difference Threshold: estimates a detectable level difference in decibels.

## Requirements

- Python 3.11 or newer
- Streamlit and the dependencies declared in `pyproject.toml`
- A modern browser with audio playback support

[`uv`](https://docs.astral.sh/uv/) is the recommended environment and dependency manager.

## Install and Run

```sh
uv python install 3.11
uv sync
uv run streamlit run app.py
```

Open `http://localhost:8501` if the browser does not open automatically. A conventional
virtual environment can also be used after installing the dependencies from
`pyproject.toml`; launch it with:

```sh
streamlit run app.py
```

## Adaptive 3AFC Method

Sound Gap Detection, Pitch Difference Threshold, and Amplitude Difference Threshold use
three-alternative forced-choice trials: two intervals are references and one randomized
interval contains the target. The shared staircase follows a 2-down-1-up rule, reducing
the difference after two consecutive correct responses and increasing it after one
incorrect response. Step size decreases at reversals. Each run ends after exactly six
reversals, and the final threshold is the mean of the last four reversal values.

## Privacy and Safety

Results remain in the local Streamlit session.
The application does not write participant results to disk, upload them, or send them to
external services.

These experiments are for educational use only. They are not medically validated and
must not be used for diagnosis. Participants may stop at any time. For audio tests, begin
at a comfortable low system volume, keep it fixed during a run, and stop immediately if
sound becomes uncomfortable. Consumer playback equipment can also limit audible results.

## Development Checks

```sh
uv run ruff check .
uv run pytest
```

Additional setup and troubleshooting guidance is available in `docs/install.md`.
