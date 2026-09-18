"""
Offline Tests for Indic Language Baseline Evaluation

Tests manifest schema structure, summary aggregation logic, and flag validation
without mocking model scores or faking ML model results.
"""

import os
import sys
import json
import unittest
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from scripts.evaluate_indic_language_baseline import compute_group_summary


class TestIndicLanguageBaselineOffline(unittest.TestCase):

    def test_manifest_file_structure(self):
        """Verify the local benchmark manifest contains valid fields for all 10 clips across 5 languages."""
        manifest_path = backend_dir / "data" / "benchmark_indic_language" / "manifest.json"
        self.assertTrue(manifest_path.exists(), "manifest.json file must exist")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(len(manifest), 10, "Manifest must contain exactly 10 clips")

        required_keys = {
            "language",
            "language_code",
            "speaker_id",
            "gender",
            "utterance_id",
            "filename",
            "relative_path",
            "dataset",
            "licence",
            "genuine_confirmation",
        }

        languages = set()
        for entry in manifest:
            self.assertTrue(required_keys.issubset(entry.keys()))
            self.assertEqual(entry["dataset"], "Google FLEURS")
            self.assertEqual(entry["licence"], "CC BY 4.0")
            languages.add(entry["language_code"])

        expected_languages = {"hi_in", "gu_in", "bn_in", "ta_in", "te_in"}
        self.assertEqual(languages, expected_languages)

    def test_compute_group_summary_calculations(self):
        """Verify mean, median, min, max, alert counts, and flag counts calculations."""
        sample_results = [
            {
                "chunk_score": 0.04,
                "alert_level": "low",
                "public_flags": ["short_audio"],
                "inference_latency_sec": 0.10,
            },
            {
                "chunk_score": 0.08,
                "alert_level": "low",
                "public_flags": [],
                "inference_latency_sec": 0.12,
            },
            {
                "chunk_score": 0.15,
                "alert_level": "low",
                "public_flags": ["synthetic_artifact"],
                "inference_latency_sec": 0.14,
            },
        ]

        summary = compute_group_summary(sample_results)

        self.assertEqual(summary["count"], 3)
        self.assertAlmostEqual(summary["mean_chunk_score"], 0.09, places=4)
        self.assertAlmostEqual(summary["median_chunk_score"], 0.08, places=4)
        self.assertEqual(summary["min_chunk_score"], 0.04)
        self.assertEqual(summary["max_chunk_score"], 0.15)
        self.assertEqual(summary["alert_counts"]["low"], 3)
        self.assertEqual(summary["alert_counts"]["high"], 0)
        self.assertEqual(summary["synthetic_artifact_flag_count"], 1)
        self.assertAlmostEqual(summary["avg_inference_latency_sec"], 0.12, places=4)

    def test_compute_group_summary_empty(self):
        """Verify graceful empty input handling for compute_group_summary."""
        self.assertEqual(compute_group_summary([]), {})


if __name__ == "__main__":
    unittest.main()
