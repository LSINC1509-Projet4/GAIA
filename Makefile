run:
	python3 run.py

test:
	pytest tests/test_coverage.py -v

coverage:
	pytest tests/test_coverage.py -v --cov=app --cov-report=term-missing

reset:
	rm -f gaia.db
	python3 -m tests.test_db

seed: reset
	python3 -m tests.test_arbre
	python3 -m tests.test_posts

demo: reset
	python3 -m tests.seed_demo

clean:
	rm -f gaia.db .coverage
	rm -rf .pytest_cache __pycache__