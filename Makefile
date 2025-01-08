lint:
	black --check --diff .
	isort --check-only .

format:
	isort .
	black .

test:
	pytest tests
	coverage run -m pytest --failed-first -vv
	coverage report -m