#!/usr/bin/env bash
set -euo pipefail
[ -f .env ] || cp .env.example .env
mkdir -p .storage exports logs sample_data/generated_cases sample_data/ground_truth metrics docs/screenshots
python scripts/generate_synthetic_docs.py --out sample_data/generated_cases --truth sample_data/ground_truth
python scripts/evaluate_pipeline.py --ground-truth sample_data/ground_truth --out metrics
echo "Now run backend and frontend using README commands."
