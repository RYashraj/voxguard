"""
VoxGuard Indian Language Baseline Evaluation Script

Evaluates VoxGuard's current real Spectra-AASIST3 ML model on genuine speech samples across
5 Indian languages (Hindi, Gujarati, Bengali, Tamil, Telugu) from the Google FLEURS benchmark dataset.

Measures baseline observed false-positive rates on genuine non-English audio without altering any model
thresholds or scores. Does NOT measure or claim multilingual deepfake detection accuracy.
"""

import os
import sys
import time
import json
import wave
import math
import statistics
import argparse
from pathlib import Path
from typing import Dict, Any, List

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.ml.ml_model import analyze_chunk, parse_audio_bytes
from app.ml.flag_filters import PROSODY_ONLY_FLAGS


def compute_group_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Computes summary statistics for a list of clip results."""
    if not results:
        return {}

    scores = [r["chunk_score"] for r in results]
    latencies = [r["inference_latency_sec"] for r in results]
    alerts = [r["alert_level"] for r in results]
    
    sorted_scores = sorted(scores)
    n = len(sorted_scores)
    median_score = (
        (sorted_scores[n // 2 - 1] + sorted_scores[n // 2]) / 2.0
        if n % 2 == 0
        else sorted_scores[n // 2]
    )

    synthetic_artifact_count = sum(
        1 for r in results if "synthetic_artifact" in r["public_flags"]
    )

    return {
        "count": n,
        "mean_chunk_score": round(statistics.mean(scores), 4),
        "median_chunk_score": round(median_score, 4),
        "min_chunk_score": round(min(scores), 4),
        "max_chunk_score": round(max(scores), 4),
        "alert_counts": {
            "low": alerts.count("low"),
            "medium": alerts.count("medium"),
            "high": alerts.count("high"),
        },
        "synthetic_artifact_flag_count": synthetic_artifact_count,
        "avg_inference_latency_sec": round(statistics.mean(latencies), 4),
    }


def run_evaluation(manifest_path: Path) -> Dict[str, Any]:
    """Runs real ML model analysis on all clips in the manifest."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    if not isinstance(manifest, list):
        raise ValueError("Manifest must contain a list of clip objects")

    clip_results = []
    language_groups: Dict[str, List[Dict[str, Any]]] = {}

    for entry in manifest:
        rel_path = entry.get("relative_path") or entry.get("filename")
        full_path = backend_dir / rel_path
        if not full_path.exists():
            full_path = manifest_path.parent / entry.get("filename", "")

        if not full_path.exists():
            raise FileNotFoundError(f"Audio clip file not found: {full_path}")

        with open(full_path, "rb") as f:
            audio_bytes = f.read()

        # Measure audio duration
        duration_sec = 0.0
        try:
            with wave.open(str(full_path), "rb") as wav:
                duration_sec = round(wav.getnframes() / float(wav.getframerate()), 2)
        except Exception:
            duration_sec = 0.0

        # Measure real ML inference latency
        t0 = time.perf_counter()
        analysis = analyze_chunk(audio_bytes)
        t1 = time.perf_counter()
        latency_sec = round(t1 - t0, 4)

        public_flags = analysis.get("flags", [])
        
        # Ensure no prosody-only flags appear in public output
        for flag in public_flags:
            if flag in PROSODY_ONLY_FLAGS:
                raise ValueError(
                    f"Quarantined prosody flag '{flag}' detected in public output for {entry.get('filename')}"
                )

        res = {
            "language": entry["language"],
            "language_code": entry.get("language_code", ""),
            "speaker_id": entry.get("speaker_id", ""),
            "gender": entry.get("gender", ""),
            "utterance_id": entry.get("utterance_id", ""),
            "filename": entry.get("filename", ""),
            "duration_sec": duration_sec,
            "chunk_score": float(analysis.get("chunk_score", 0.0)),
            "confidence": float(analysis.get("confidence", 0.0)),
            "public_flags": public_flags,
            "alert_level": analysis.get("alert_level", "low"),
            "inference_latency_sec": latency_sec,
        }

        clip_results.append(res)
        lang_key = entry["language"]
        if lang_key not in language_groups:
            language_groups[lang_key] = []
        language_groups[lang_key].append(res)

    # Compute summaries
    overall_summary = compute_group_summary(clip_results)
    per_language_summary = {
        lang: compute_group_summary(items)
        for lang, items in language_groups.items()
    }

    high_risk_false_positives = sum(
        1 for r in clip_results if r["alert_level"] == "high"
    )

    conclusion = (
        "No high-risk false positives observed in this small genuine-speech sample"
        if high_risk_false_positives == 0
        else f"High-risk false positives were observed ({high_risk_false_positives} clip(s)); model limitations must be disclosed."
    )

    report = {
        "dataset_name": "Google FLEURS",
        "dataset_url": "https://huggingface.co/datasets/google/fleurs",
        "licence": "CC BY 4.0",
        "total_clips": len(clip_results),
        "high_risk_false_positives_count": high_risk_false_positives,
        "conclusion": conclusion,
        "per_clip_results": clip_results,
        "per_language_summary": per_language_summary,
        "overall_summary": overall_summary,
    }

    return report


def print_report_tables(report: Dict[str, Any]):
    """Prints clean ASCII markdown tables of evaluation results."""
    print("\n================================================================================")
    print("VOXGUARD INDIAN LANGUAGE BASELINE EVALUATION REPORT")
    print("================================================================================\n")
    print(f"Dataset: {report['dataset_name']} ({report['dataset_url']})")
    print(f"Licence: {report['licence']}")
    print(f"Total Clips Evaluated: {report['total_clips']}")
    print(f"Conclusion: {report['conclusion']}\n")

    print("--- PER-CLIP RESULTS ---")
    print("| Language | Utterance ID | Gender | Duration (s) | Score | Alert | Flags | Latency (s) |")
    print("|---|---|---|---|---|---|---|---|")
    for r in report["per_clip_results"]:
        flags_str = ", ".join(r["public_flags"]) if r["public_flags"] else "none"
        print(
            f"| {r['language']} | {r['utterance_id']} | {r['gender']} | {r['duration_sec']} | "
            f"{r['chunk_score']:.4f} | {r['alert_level']} | {flags_str} | {r['inference_latency_sec']:.3f} |"
        )

    print("\n--- PER-LANGUAGE SUMMARY ---")
    print("| Language | Count | Mean Score | Median Score | Min Score | Max Score | Low / Med / High | Latency (s) |")
    print("|---|---|---|---|---|---|---|---|")
    for lang, summary in report["per_language_summary"].items():
        alerts = summary["alert_counts"]
        alert_str = f"{alerts['low']} / {alerts['medium']} / {alerts['high']}"
        print(
            f"| {lang} | {summary['count']} | {summary['mean_chunk_score']:.4f} | "
            f"{summary['median_chunk_score']:.4f} | {summary['min_chunk_score']:.4f} | "
            f"{summary['max_chunk_score']:.4f} | {alert_str} | {summary['avg_inference_latency_sec']:.3f} |"
        )
    print("\n================================================================================\n")


def main():
    parser = argparse.ArgumentParser(
        description="Run VoxGuard Indic Language Baseline Evaluation"
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default="data/benchmark_indic_language/manifest.json",
        help="Path to manifest JSON file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional path to save JSON report",
    )

    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = backend_dir / manifest_path

    # Force real ML mode env check notice
    os.environ["VOXGUARD_ML_MODE"] = "real"

    report = run_evaluation(manifest_path)
    print_report_tables(report)

    if args.output:
        out_path = Path(args.output)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Report JSON saved to: {out_path}")


if __name__ == "__main__":
    main()
