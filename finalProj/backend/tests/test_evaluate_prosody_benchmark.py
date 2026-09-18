"""
Offline Unit Tests for Prosody Benchmark Evaluation Script

Verifies that `evaluate_prosody_benchmark.py` runs safely offline, returns structured
telemetry for bonafide and spoof clips, handles missing files gracefully, and does
not invoke external neural models.
"""

import os
import sys
import pytest

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.evaluate_prosody_benchmark import evaluate_audio_files, print_summary_table


def test_evaluate_audio_files_with_existing_clips():
    """Tests evaluation on existing bonafide and spoof benchmark clips."""
    ref_clip = "data/benchmark_speaker_calibration/reference_speaker/LA_0030_ref_LA_E_5849185.wav"
    spoof_clip = "data/test_audio/asvspoof_spoof_clips/LA_E_2834763.wav"

    if os.path.exists(ref_clip) and os.path.exists(spoof_clip):
        results = evaluate_audio_files([ref_clip, spoof_clip], "test_label")

        assert len(results) == 2
        for r in results:
            assert r["status"] == "ok"
            assert r["duration_sec"] > 0.0
            assert "pitch_mean_hz" in r
            assert "voiced_ratio" in r
            assert "prosody_score" in r
            assert isinstance(r["flags"], list)


def test_evaluate_audio_files_missing_file_handling():
    """Tests graceful error reporting when a file path does not exist."""
    fake_path = "data/non_existent_audio_file.wav"
    results = evaluate_audio_files([fake_path], "missing_test")

    assert len(results) == 1
    assert results[0]["status"] == "missing_file"
    assert "missing_file" in results[0]["flags"]


def test_summary_table_formatting(capsys):
    """Verifies that print_summary_table executes without raising errors."""
    mock_rows = [
        {
            "file": "mock1.wav",
            "label": "bonafide",
            "status": "ok",
            "duration_sec": 3.0,
            "pitch_mean_hz": 120.0,
            "pitch_std_hz": 15.0,
            "voiced_ratio": 0.5,
            "pause_ratio": 0.2,
            "speech_rate_proxy": 4.0,
            "prosody_score": 0.05,
            "flags": [],
            "reason_codes": []
        }
    ]

    print_summary_table(mock_rows, "Mock Test")
    captured = capsys.readouterr()
    assert "MOCK TEST GROUP SUMMARY" in captured.out
    assert "F0 Mean (Hz)" in captured.out
