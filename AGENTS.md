## Assignment Requirements

The application must include exactly these six sensory tests:
1. Contrast Sensitivity
2. Smallest Noticeable Size
3. Pitch Frequency Range
4. Sound Gap Detection
5. Pitch Difference Threshold
6. Amplitude Difference Threshold

### Visual Tests
- Contrast sensitivity must progressively reduce stimulus contrast.
- Report estimated contrast sensitivity as a percentage.
- Include interpretation related to display bit resolution and human factors.
- Smallest noticeable size must use screen physical dimensions,
  screen pixel resolution, and viewing distance.
- Calculate angular resolution in arcminutes.

### Auditory Tests
- Pitch frequency range must allow testing from approximately 20 Hz to 20 kHz.
- Highest audible frequency must be recorded to at least 50 Hz resolution.
- Gap detection threshold must be reported in milliseconds.
- Pitch difference threshold must be reported in Hz.
- Amplitude difference threshold must be reported in dB.

### 3AFC Requirements
For gap, pitch difference, and amplitude difference:
- Present exactly 3 options per trial.
- Two options are references and one is the target.
- Randomize the target position.
- Use shared 2-down-1-up staircase logic.
- Stop after exactly 6 reversals.
- Threshold = mean of final 4 reversal values.
- Generate a final plot showing:
  - trial number
  - stimulus parameter/difference
  - response correctness
  - final estimated threshold

### Human Subjects / Safety
- Display that the tests are educational only and not diagnostic.
- Inform participants they may stop at any time.
- Do not transmit sensory data to external servers.
