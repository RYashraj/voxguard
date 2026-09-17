# Indian Accent Smoke Test

This script evaluates VoxGuard's accuracy on Indian accents by running genuine and cloned voice samples through the real ML inference pipeline (Spectra-AASIST3).

## Setup

1. Create a `data/accent_clips` directory inside the `scripts` folder (it will be auto-created when you run the script once).
2. Gather 5-10 short (3–5 second) WAV clips of teammates speaking in English with varied Indian accents, Hindi, Gujarati, etc.
3. Name genuine clips with the `genuine_` prefix (e.g., `genuine_yashraj_hindi.wav`).
4. Generate cloned AI clips of the same voices and name them with the `cloned_` prefix (e.g., `cloned_yashraj_hindi.wav`).
5. Place all these `.wav` files into `scripts/data/accent_clips/`.

## Running the Evaluation

Ensure your backend virtual environment is active so ML dependencies are available.

```bash
cd scripts
python accent_smoke_test.py
```

## Results

The script will process each clip and generate an `accent_eval_results.md` file in the `scripts/` directory containing a table of scores, flags, and the overall accuracy rate. You can use these numbers in your pitch to prove the system works on regional accents!
