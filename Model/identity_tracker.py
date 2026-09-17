import torch.nn.functional as F

from speaker_test import get_embedding


class SessionIdentityTracker:

    def __init__(self, reference_embedding):
        self.reference_embedding = reference_embedding

    def compare(self, audio_file):
        current_embedding = get_embedding(audio_file)

        similarity = F.cosine_similarity(
            self.reference_embedding.squeeze(),
            current_embedding.squeeze(),
            dim=0
        )

        similarity = similarity.item()

        identity_drift = 1 - similarity

        return similarity, identity_drift