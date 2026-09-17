import os
import sys
import glob

# Append the backend folder to sys.path so we can import the ML pipeline
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

try:
    from app.ml.ml_model import analyze_chunk
except ImportError:
    print("Error: Could not import analyze_chunk from backend/app/ml/ml_model.py.")
    print("Ensure you are running this from the project root or the scripts directory.")
    sys.exit(1)

def run_smoke_test():
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, "data", "accent_clips")
    output_md = os.path.join(base_dir, "accent_eval_results.md")
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created directory {data_dir}.")
        print("Please place .wav files here following the naming convention:")
        print(" genuine_<name>.wav or cloned_<name>.wav")
        return

    wav_files = glob.glob(os.path.join(data_dir, "*.wav"))
    if not wav_files:
        print(f"No WAV files found in {data_dir}. Drop some files there and run again.")
        return

    results = []
    correct_count = 0
    total_count = len(wav_files)

    for file_path in sorted(wav_files):
        filename = os.path.basename(file_path)
        # Determine expected label based on filename prefix
        is_genuine = filename.lower().startswith("genuine_")
        
        with open(file_path, "rb") as f:
            audio_bytes = f.read()

        print(f"Analyzing {filename}...")
        try:
            # Force the model to load if it hasn't
            result = analyze_chunk(audio_bytes)
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue
        
        chunk_score = result.get("chunk_score", 0.5)
        # For our ML logic, < 0.40 is considered genuine, >= 0.70 is synthetic/cloned
        # We'll use > 0.5 as a simple threshold for binary evaluation
        predicted_synthetic = chunk_score > 0.50
        
        # is_genuine=True means NOT synthetic
        expected_synthetic = not is_genuine
        
        is_correct = predicted_synthetic == expected_synthetic
        if is_correct:
            correct_count += 1
            
        results.append({
            "filename": filename,
            "expected_synthetic": expected_synthetic,
            "predicted_synthetic": predicted_synthetic,
            "chunk_score": chunk_score,
            "confidence": result.get("confidence", 0.0),
            "flags": result.get("flags", []),
            "is_correct": is_correct
        })

    # Write output to Markdown
    with open(output_md, "w", encoding="utf-8") as f:
        f.write("# Accent Smoke Test Results\n\n")
        f.write(f"**Summary:** {correct_count}/{total_count} correctly flagged.\n\n")
        
        f.write("| File | Expected | Predicted | Risk Score | Confidence | Flags | Correct? |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        
        for res in results:
            exp_str = "Cloned" if res["expected_synthetic"] else "Genuine"
            pred_str = "Cloned" if res["predicted_synthetic"] else "Genuine"
            correct_str = "✅ Yes" if res["is_correct"] else "❌ No"
            flags_str = ", ".join(res["flags"]) if res["flags"] else "None"
            
            f.write(f"| {res['filename']} | {exp_str} | {pred_str} | {res['chunk_score']:.4f} | {res['confidence']:.4f} | {flags_str} | {correct_str} |\n")

    print(f"Done. Wrote results to {output_md}")

if __name__ == "__main__":
    # Force real model mode for the smoke test regardless of .env
    os.environ["VOXGUARD_ML_MODE"] = "real"
    print("Running Indian Accent Smoke Test...")
    run_smoke_test()
