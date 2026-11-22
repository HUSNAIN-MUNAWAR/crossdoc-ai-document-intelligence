SHELL := /bin/bash
setup:
	bash scripts/setup_local.sh
dev:
	@echo "Backend: cd backend && uvicorn app.main:app --reload --port 8000"
	@echo "Frontend: cd frontend && npm run dev"
docker-up:
	docker compose up --build
docker-down:
	docker compose down
ocr-check:
	python scripts/check_ocr_engines.py
ocr-smoke:
	python scripts/validate_real_ocr.py
install-ocr:
	bash scripts/install_ocr_dependencies.sh
seed:
	python scripts/seed_demo_data.py
generate-docs:
	python scripts/generate_synthetic_docs.py --out sample_data/generated_cases --truth sample_data/ground_truth
process-demo:
	python scripts/process_demo_case.py
evaluate:
	python scripts/evaluate_pipeline.py --sample-data sample_data/generated_cases --ground-truth sample_data/ground_truth --out metrics
screenshots:
	cd frontend && npm run screenshots
test:
	cd backend && pytest -q
animation:
	python scripts/generate_reconciliation_animation.py
runtime-evidence:
	python scripts/generate_real_runtime_video.py
lint:
	cd backend && python -m compileall app
frontend-build:
	cd frontend && npm run build
docker-config:
	docker compose config >/dev/null
