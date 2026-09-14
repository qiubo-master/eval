.PHONY: install api test lint validate-datasets offline-eval redteam langfuse-up langfuse-down

install:
	python -m pip install -e '.[eval,dev]'

api:
	uvicorn llm_eval_system.api:app --reload

test:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q

lint:
	ruff check .

validate-datasets:
	python scripts/validate_datasets.py

offline-eval:
	python evals/run_offline.py --threshold 0.75

redteam:
	npx promptfoo@latest redteam run -c promptfoo/promptfooconfig.yaml

langfuse-up:
	docker compose -f docker-compose.langfuse.yml up -d

langfuse-down:
	docker compose -f docker-compose.langfuse.yml down
