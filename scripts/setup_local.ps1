if (!(Test-Path .env)) { Copy-Item .env.example .env }
New-Item -ItemType Directory -Force -Path .storage, exports, logs, sample_data/generated_cases, sample_data/ground_truth, metrics, docs/screenshots | Out-Null
python scripts/generate_synthetic_docs.py --out sample_data/generated_cases --truth sample_data/ground_truth
python scripts/evaluate_pipeline.py --ground-truth sample_data/ground_truth --out metrics
