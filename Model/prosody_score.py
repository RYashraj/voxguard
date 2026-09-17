import librosa
import numpy as np


# ============================================================
# FEATURE EXTRACTION
# ============================================================

def extract_prosody_features(file_path):

    audio, sample_rate = librosa.load(
        file_path,
        sr=16000,
        mono=True
    )

    # --------------------------------------------------------
    # 1. Pitch variation
    # --------------------------------------------------------

    pitch, voiced_flag, voiced_probs = librosa.pyin(
        audio,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7"),
        sr=sample_rate
    )

    pitch_values = pitch[~np.isnan(pitch)]

    if len(pitch_values) == 0:
        pitch_variation = 0.0
    else:
        pitch_variation = float(np.std(pitch_values))

    # --------------------------------------------------------
    # 2. Silence duration
    # --------------------------------------------------------

    intervals = librosa.effects.split(
        audio,
        top_db=30
    )

    voiced_duration = sum(
        (end - start) / sample_rate
        for start, end in intervals
    )

    total_duration = len(audio) / sample_rate

    silence_duration = (
        total_duration - voiced_duration
    )

    # --------------------------------------------------------
    # 3. Jitter
    # --------------------------------------------------------

    if len(pitch_values) > 1:

        periods = 1 / pitch_values

        period_differences = np.abs(
            np.diff(periods)
        )

        mean_period = np.mean(periods)

        if mean_period != 0:
            jitter = (
                np.mean(period_differences)
                / mean_period
            )
        else:
            jitter = 0.0

    else:
        jitter = 0.0

    # --------------------------------------------------------
    # 4. Shimmer
    # --------------------------------------------------------

    amplitudes = []
    current_sample = 0

    if len(pitch_values) > 0:

        periods = 1 / pitch_values

        for period in periods:

            cycle_length = int(
                period * sample_rate
            )

            if cycle_length <= 0:
                continue

            if (
                current_sample + cycle_length
                > len(audio)
            ):
                break

            cycle = audio[
                current_sample:
                current_sample + cycle_length
            ]

            rms = np.sqrt(
                np.mean(cycle ** 2)
            )

            amplitudes.append(rms)

            current_sample += cycle_length

    amplitudes = np.array(amplitudes)

    if (
        len(amplitudes) > 1
        and np.mean(amplitudes) != 0
    ):

        amplitude_differences = np.abs(
            np.diff(amplitudes)
        )

        shimmer = (
            np.mean(amplitude_differences)
            / np.mean(amplitudes)
        )

    else:
        shimmer = 0.0

    return {
        "pitch_variation": float(pitch_variation),
        "silence_duration": float(silence_duration),
        "jitter": float(jitter),
        "shimmer": float(shimmer)
    }


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_feature(value, minimum, maximum):

    if maximum == minimum:
        return 0.0

    normalized = (
        value - minimum
    ) / (
        maximum - minimum
    )

    return float(
        np.clip(normalized, 0.0, 1.0)
    )


# ============================================================
# EXPERIMENTAL PROSODY SCORE
# ============================================================

def calculate_prosody_score(features):

    pitch_score = normalize_feature(
        features["pitch_variation"],
        0.0,
        100.0
    )

    silence_score = normalize_feature(
        features["silence_duration"],
        0.0,
        3.0
    )

    jitter_score = normalize_feature(
        features["jitter"],
        0.0,
        0.10
    )

    shimmer_score = normalize_feature(
        features["shimmer"],
        0.0,
        0.50
    )

    score = (
        0.25 * pitch_score
        + 0.25 * silence_score
        + 0.25 * jitter_score
        + 0.25 * shimmer_score
    )

    return float(
        np.clip(score * 100, 0.0, 100.0)
    )


# ============================================================
# BACKEND FUNCTION
# ============================================================

def prosody_score(audio_path, language="english"):

    language = language.lower().strip()

    if language not in ["english", "gujarati"]:
        raise ValueError(
            "Unsupported language. "
            "Use 'english' or 'gujarati'."
        )

    features = extract_prosody_features(
        audio_path
    )

    score = calculate_prosody_score(
        features
    )

    return {
        "prosody_score": round(score, 2),

        "features": {
            "pitch_variation": round(
                features["pitch_variation"],
                4
            ),

            "silence_duration": round(
                features["silence_duration"],
                4
            ),

            "jitter": round(
                features["jitter"],
                4
            ),

            "shimmer": round(
                features["shimmer"],
                4
            )
        },

        "language": language
    }