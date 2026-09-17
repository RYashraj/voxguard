import torch
import wave
import numpy as np
from speechbrain.inference.speaker import EncoderClassifier

print("Loading ECAPA-TDNN model...")

classifier = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb"
)

print("Model loaded successfully!")


def get_embedding(file_path):
    with wave.open(file_path, "rb") as wf:
        sample_rate = wf.getframerate()
        num_frames = wf.getnframes()
        num_channels = wf.getnchannels()
        audio_bytes = wf.readframes(num_frames)

    audio_np = np.frombuffer(audio_bytes, dtype=np.int16)

    if num_channels > 1:
        audio_np = audio_np.reshape(-1, num_channels).mean(axis=1)

    audio = torch.from_numpy(audio_np.copy()).float() / 32768.0
    audio = audio.unsqueeze(0)

    embedding = classifier.encode_batch(audio)

    return embedding


reference = get_embedding("test_audio/guj.wav")

test_files = [
    "test_audio/1_clone.wav",
    "test_audio/2_clone.wav",
    "test_audio/1_real_np.wav",
]

print("\n==============================")
print("IDENTITY DRIFT VALIDATION")
print("==============================")

for file in test_files:

    current_embedding = get_embedding(file)

    similarity = torch.nn.functional.cosine_similarity(
        reference.squeeze(),
        current_embedding.squeeze(),
        dim=0
    )

    identity_drift = 1 - similarity.item()

    print(f"\nFile: {file}")
    print(f"Cosine similarity: {similarity.item():.4f}")
    print(f"Identity drift: {identity_drift:.4f}")