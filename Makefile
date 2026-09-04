.PHONY: setup run test evaluate check

setup:
	python -m pip install -r requirements.txt

run:
	uvicorn backend.app.main:app --reload

test:
	python -m unittest discover -s tests -v

evaluate:
	python scripts/evaluate.py

check: test evaluate
