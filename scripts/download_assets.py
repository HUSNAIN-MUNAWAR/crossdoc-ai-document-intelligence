import subprocess, sys
subprocess.run([sys.executable,"scripts/generate_synthetic_docs.py","--out","sample_data/generated_cases","--truth","sample_data/ground_truth"], check=True)
