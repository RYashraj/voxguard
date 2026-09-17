import numpy as np
from pathlib import Path

from prosody_score import extract_prosody_features


# ============================================================
# PROSODY TEST - ONE AUDIO FOLDER
# ============================================================

# CHANGE THIS PATH WHEN TESTING A DIFFERENT DATASET
audio_folder = Path("test_audio/clone_audios")


# Find all WAV files inside folder and subfolders
audio_files = list(audio_folder.rglob("*.wav"))

print("Number of samples:", len(audio_files))

results = []


# ============================================================
# EXTRACT FEATURES
# ============================================================

for file in audio_files:

    features = extract_prosody_features(
        str(file)
    )

    results.append({
        "file": str(file),
        **features
    })


# ============================================================
# PRINT RESULTS
# ============================================================

print("\n================================")
print("PROSODY FEATURE DATASET")
print("================================")


for result in results:

    print(f"\n{result['file']}")

    print(
        f"Pitch: "
        f"{result['pitch_variation']:.2f} Hz"
    )

    print(
        f"Silence: "
        f"{result['silence_duration']:.3f} s"
    )

    print(
        f"Jitter: "
        f"{result['jitter'] * 100:.2f}%"
    )

    print(
        f"Shimmer: "
        f"{result['shimmer'] * 100:.2f}%"
    )


# ============================================================
# STATISTICS
# ============================================================

features_to_analyze = [
    "pitch_variation",
    "silence_duration",
    "jitter",
    "shimmer"
]


print("\n================================")
print("SPEECH STATISTICS")
print("================================")


for feature in features_to_analyze:

    values = [
        result[feature]
        for result in results
    ]

    print(f"\n{feature}")

    print(
        f"Mean = "
        f"{np.mean(values):.4f}"
    )

    print(
        f"Min  = "
        f"{np.min(values):.4f}"
    )

    print(
        f"Max  = "
        f"{np.max(values):.4f}"
    )