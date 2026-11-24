PYTHON ?= python3

.PHONY: help test lint typecheck check dist docs-sync clean

help:
	@echo "make test       - lance les tests (unittest, stdlib, aucune installation)"
	@echo "make lint       - ruff check . (optionnel : pip install -e '.[dev]')"
	@echo "make typecheck  - pyright (optionnel)"
	@echo "make check      - test + lint + typecheck"
	@echo "make dist       - assemble dist/leekwars/ (main.py + libs/) pour l'import Leek Wars"
	@echo "make docs-sync  - rafraîchit docs/encyclopedia/ depuis le site Leek Wars"

test:
	$(PYTHON) -m unittest discover -s tests -v

lint:
	ruff check .

typecheck:
	pyright

check: test lint typecheck

dist:
	$(PYTHON) tools/build_dist.py

docs-sync:
	$(PYTHON) tools/sync_encyclopedia.py

clean:
	rm -rf dist
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
