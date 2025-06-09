install:
	pip install -e .[test]

lint:
	flake8 .

test:
	python -m jarvus_app.llm.test_client

run:
	python run_dev.py 