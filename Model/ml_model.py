import numpy as np
import torch
import torchaudio
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

SAMPLE_RATE = 16000
AUDIO_FILE = r"test_audio\clone_2.wav"


def load_audio():
    import wave

    with wave.open(AUDIO_FILE, "rb") as wav:
        sample_rate = wav.getframerate()
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        frames = wav.readframes(wav.getnframes())

    if sample_width == 2:
        audio = np.frombuffer(
            frames, dtype=np.int16
        ).astype(np.float32) / 32768.0

    elif sample_width == 4:
        audio = np.frombuffer(
            frames, dtype=np.int32
        ).astype(np.float32) / 2147483648.0

    else:
        raise ValueError(
            f"Unsupported WAV sample width: {sample_width} bytes"
        )

    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)

    if sample_rate != SAMPLE_RATE:
        waveform = torch.tensor(audio).unsqueeze(0)

        waveform = torchaudio.functional.resample(
            waveform,
            sample_rate,
            SAMPLE_RATE
        )

        audio = waveform.squeeze(0).numpy()

    return audio


def test_bisher(audio):
    print("\n===== BISHER MODEL =====")

    model_id = "Bisher/wav2vec2_ASV_deepfake_audio_detection"

    extractor = AutoFeatureExtractor.from_pretrained(model_id)
    model = AutoModelForAudioClassification.from_pretrained(model_id)
    model.eval()

    inputs = extractor(
        audio,
        sampling_rate=SAMPLE_RATE,
        return_tensors="pt"
    )

    with torch.no_grad():
        logits = model(**inputs).logits
        probabilities = torch.softmax(logits, dim=-1)[0]

    labels = model.config.id2label

    for i, probability in enumerate(probabilities):
        print(f"{labels[i]}: {probability.item():.4f}")

    prediction = labels[torch.argmax(probabilities).item()]
    print(f"Prediction: {prediction.upper()}")


def test_spectra(audio):
    print("\n===== SPECTRA-AASIST3 =====")

    import sys

    model_path = r"C:\Users\NANDINI\.cache\huggingface\hub\models--lab260--Spectra-AASIST3\snapshots\bc0ded888080ddad493177bb53aa6f5b95219d7c"

    sys.path.insert(0, model_path)

    from model import SpectraAASIST3

    model = SpectraAASIST3.from_pretrained(model_path)
    model.eval()

    required_samples = 64600

    if len(audio) < required_samples:
        repeats = int(np.ceil(required_samples / len(audio)))
        audio = np.tile(audio, repeats)

    audio = audio[:required_samples]

    waveform = torch.tensor(
        audio,
        dtype=torch.float32
    ).unsqueeze(0)

    with torch.no_grad():
        output = model(waveform)

    print("Raw model output:")
    print(output)

    probabilities = torch.softmax(output, dim=-1)[0]

    print("Spectra probabilities:")
    print(f"Class 0: {probabilities[0].item():.4f}")
    print(f"Class 1: {probabilities[1].item():.4f}")


if __name__ == "__main__":

    print("Loading:", AUDIO_FILE)

    audio = load_audio()

    print(f"Sample rate: {SAMPLE_RATE} Hz")
    print(f"Duration: {len(audio) / SAMPLE_RATE:.2f} seconds")

    test_bisher(audio)
    test_spectra(audio)