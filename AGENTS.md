# AGENTS.md — Perceptual Sense Lab

## Project Overview
This is a Streamlit web application for measuring human sensory thresholds
(visual and auditory). It is a psychology/engineering assignment.

## Tech Stack
- Python 3.10+
- Streamlit (multi-page app structure under /pages/)
- numpy, scipy (audio generation)
- matplotlib (result plots)
- Pillow / PIL (visual stimulus rendering)
- base64 + st.audio() for in-browser audio playback

## Key Constraints
- Do NOT use sounddevice or pyaudio — they do not work in a browser context.
  All audio must be generated as WAV bytes, base64-encoded, and passed to st.audio().
- All adaptive tests (gap, pitch, amplitude) must use the shared
  utils/adaptive.py staircase logic. Do not duplicate this logic per test.
- The 2-down-1-up staircase ends after exactly 6 reversal points.
  The threshold is the average of the last 4 reversal values.
- Each 3AFC trial presents 3 audio options: the participant clicks 1, 2, or 3.
- All tests must save results to data/results.json.

## Testing
- After implementing any module, confirm it runs with: streamlit run app.py
- There are no automated test files yet — manual verification only.

## File Naming
- Pages follow Streamlit naming: 01_name.py, 02_name.py, etc.
- Utility functions go in utils/, not in page files.
